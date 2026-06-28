// ============================================================================
// 11 — Zero-copy wire decoding: read a fixed-layout binary feed in place
// Run:  cargo run --release --example 11_zero_copy_wire
// (No C++ counterpart — the cpp README lists "custom zero-copy serialization" as
//  a production direction; here's the Rust take.)
// ----------------------------------------------------------------------------
// Binary exchange feeds (ITCH/OUCH/SBE-style) are fixed-layout records. The fast
// path doesn't parse field-by-field into an owned struct — it overlays the struct
// directly on the received bytes and reads fields in place. No allocation, no copy.
//
// Why this is a good fit for Rust:
//   * `#[repr(C)]` with byte-array fields gives a guaranteed layout AND alignment
//     of 1, so the view can be cast from ANY `&[u8]` of the right length — no
//     alignment hazard, no `unsafe` leaking to the caller.
//   * The `unsafe` cast is wrapped behind a safe `parse()` that checks length and
//     returns `Option<&Msg>`: a borrow tied to the buffer's lifetime, so the view
//     can never outlive the bytes it points into (the borrow checker guarantees it).
//   * Fields are network byte order; accessors convert with `from_be_bytes`.
// ============================================================================

/// An "add order" message, 22 bytes, exactly as it arrives on the wire.
/// All fields are raw big-endian byte arrays => `align_of == 1`, so a `&[u8]` can
/// be reinterpreted as `&AddOrder` with only a length check.
#[repr(C)]
struct AddOrder {
    msg_type: u8, // b'A'
    order_id: [u8; 8],
    side: u8,       // b'B' / b'S'
    price: [u8; 8], // big-endian i64, fixed-point ticks
    qty: [u8; 4],   // big-endian u32
}

impl AddOrder {
    const LEN: usize = std::mem::size_of::<Self>();

    /// Zero-copy view over `bytes`. Returns a reference INTO the buffer (no copy),
    /// or None if there aren't enough bytes. The lifetime ties the view to `bytes`.
    fn parse(bytes: &[u8]) -> Option<&AddOrder> {
        if bytes.len() < Self::LEN {
            return None;
        }
        // SAFETY: AddOrder is repr(C) with align 1 (all byte/byte-array fields), so
        // any address is suitably aligned, and we verified at least LEN bytes exist.
        Some(unsafe { &*(bytes.as_ptr() as *const AddOrder) })
    }

    // Accessors decode network byte order on demand — still no copy of the record.
    fn order_id(&self) -> u64 {
        u64::from_be_bytes(self.order_id)
    }
    fn price(&self) -> i64 {
        i64::from_be_bytes(self.price)
    }
    fn qty(&self) -> u32 {
        u32::from_be_bytes(self.qty)
    }
    fn side(&self) -> u8 {
        self.side
    }
}

// For contrast: an owned, fully-decoded struct (what a copying parser produces).
#[derive(Debug)]
struct OwnedAddOrder {
    order_id: u64,
    side: u8,
    price: i64,
    qty: u32,
}
fn parse_owned(bytes: &[u8]) -> Option<OwnedAddOrder> {
    let m = AddOrder::parse(bytes)?;
    Some(OwnedAddOrder {
        order_id: m.order_id(),
        side: m.side(),
        price: m.price(),
        qty: m.qty(),
    })
}

// Build one wire message (as a feed would send it).
fn encode(order_id: u64, side: u8, price: i64, qty: u32) -> Vec<u8> {
    let mut v = Vec::with_capacity(AddOrder::LEN);
    v.push(b'A');
    v.extend_from_slice(&order_id.to_be_bytes());
    v.push(side);
    v.extend_from_slice(&price.to_be_bytes());
    v.extend_from_slice(&qty.to_be_bytes());
    v
}

fn main() {
    println!(
        "AddOrder wire size = {} bytes, align = {}",
        AddOrder::LEN,
        std::mem::align_of::<AddOrder>()
    );

    let wire = encode(0xDEAD_BEEF, b'B', 1_234_500, 250);
    let msg = AddOrder::parse(&wire).expect("complete message");
    println!(
        "zero-copy view: type={} id={:#x} side={} price={} qty={}",
        msg.msg_type as char,
        msg.order_id(),
        msg.side() as char,
        msg.price(),
        msg.qty()
    );

    // Decode a stream of messages laid end-to-end in one buffer, summing notional —
    // all without allocating a per-message struct.
    let mut buf = Vec::new();
    for i in 0..5 {
        buf.extend(encode(
            1000 + i,
            if i % 2 == 0 { b'B' } else { b'S' },
            1_000_000 + i as i64 * 25,
            100,
        ));
    }
    let mut notional: i128 = 0;
    let mut off = 0;
    while let Some(m) = AddOrder::parse(&buf[off..]) {
        notional += m.price() as i128 * m.qty() as i128;
        off += AddOrder::LEN;
        if off >= buf.len() {
            break;
        }
    }
    println!(
        "decoded {} messages in place, total notional = {notional}",
        buf.len() / AddOrder::LEN
    );
    println!("(run `cargo bench` for zero-copy view vs owned-copy parse)");

    // The borrow checker stops you keeping a view past its buffer:
    //   let dangling = { let tmp = encode(1, b'B', 1, 1); AddOrder::parse(&tmp) };
    //   dangling.unwrap().qty();   // error: `tmp` does not live long enough
    // An owned copy, by contrast, outlives its buffer (at the cost of the copy).
    let owned = parse_owned(&wire).unwrap();
    println!(
        "owned copy (outlives buffer): id={:#x} side={} price={} qty={}",
        owned.order_id, owned.side as char, owned.price, owned.qty
    );
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_fields() {
        let wire = encode(0xABCD, b'S', -42_0000, 999);
        let m = AddOrder::parse(&wire).unwrap();
        assert_eq!(m.msg_type, b'A');
        assert_eq!(m.order_id(), 0xABCD);
        assert_eq!(m.side(), b'S');
        assert_eq!(m.price(), -42_0000);
        assert_eq!(m.qty(), 999);
    }

    #[test]
    fn rejects_short_buffer() {
        let wire = encode(1, b'B', 1, 1);
        assert!(AddOrder::parse(&wire[..AddOrder::LEN - 1]).is_none());
    }

    #[test]
    fn view_is_zero_copy_layout() {
        assert_eq!(AddOrder::LEN, 22);
        assert_eq!(std::mem::align_of::<AddOrder>(), 1); // castable from any &[u8]
    }

    #[test]
    fn owned_matches_view() {
        let wire = encode(7, b'B', 555, 33);
        let v = AddOrder::parse(&wire).unwrap();
        let o = parse_owned(&wire).unwrap();
        assert_eq!(
            (v.order_id(), v.side(), v.price(), v.qty()),
            (o.order_id, o.side, o.price, o.qty)
        );
    }
}
