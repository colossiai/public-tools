// Tier 4 — Lesson 18: Fluent builder with compile-time phantom state
//
// Goal: a builder where the type system PREVENTS you from calling `.build()`
// until every required field is set. No runtime guards needed.
//
// Trick: track "which fields have been set" in a phantom type parameter.
// Each setter returns a new builder type with that field marked as Set.

// ---------- the phantom state ----------
// A flag type per field: "Unset" or "Set".
type FieldState = "Unset" | "Set";

interface State {
    name: FieldState;
    host: FieldState;
    port: FieldState;
}

type InitialState = { name: "Unset"; host: "Unset"; port: "Unset" };
type ReadyState = { name: "Set"; host: "Set"; port: "Set" };

// helper: update one slot of the state
type Mark<S extends State, K extends keyof State> = {
    [P in keyof State]: P extends K ? "Set" : S[P];
};

// ---------- the builder ----------
class ServerBuilder<S extends State> {
    private constructor(
        private readonly data: { name?: string; host?: string; port?: number },
    ) {}

    static start(): ServerBuilder<InitialState> {
        return new ServerBuilder({});
    }

    name(value: string): ServerBuilder<Mark<S, "name">> {
        return new ServerBuilder<Mark<S, "name">>({ ...this.data, name: value });
    }
    host(value: string): ServerBuilder<Mark<S, "host">> {
        return new ServerBuilder<Mark<S, "host">>({ ...this.data, host: value });
    }
    port(value: number): ServerBuilder<Mark<S, "port">> {
        return new ServerBuilder<Mark<S, "port">>({ ...this.data, port: value });
    }

    // `build` is only callable when the phantom state is fully Set.
    // The type constraint `S extends ReadyState` enforces this *at compile time*.
    build(this: ServerBuilder<ReadyState>): { name: string; host: string; port: number } {
        return {
            name: this.data.name!,
            host: this.data.host!,
            port: this.data.port!,
        };
    }
}

function main(): void {
    const cfg = ServerBuilder.start()
        .name("api")
        .host("0.0.0.0")
        .port(8080)
        .build();
    console.log("built:", cfg);

    // Each of the following is a *compile-time* error — uncomment to see:
    // ServerBuilder.start().build();                       // missing all three
    // ServerBuilder.start().name("api").build();           // missing host & port
    // ServerBuilder.start().name("api").host("h").build(); // missing port
    //
    // The error message looks like:
    //   The 'this' context of type 'ServerBuilder<{ name: "Set"; host: "Set"; port: "Unset" }>'
    //   is not assignable to method's 'this' of type 'ServerBuilder<ReadyState>'.

    console.log("(uncomment the lines in source to see compile errors)");
}

main();
