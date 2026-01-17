# 7 optimization features

1. context.WithCancelCause + context.Cause
2. errors.Join (retain multiple original errors)
3. errors.Is / errors.As + %w (to recognize acutal errors)
4. io.WriterTo / io.ReaderFrom (make IO more performant)
5. sync.OnceFunc / sync.OnceValue 
6. atomic.Pointer[T] (for config)
7. net/http/pprof (for troubleshooting)