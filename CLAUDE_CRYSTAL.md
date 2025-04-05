Crystal Best Practices & Gotchas:

    initialize: Only for .new constructor. Don't name regular methods initialize.
    Types: Strict. Declare explicitly. Use Unions (|) and nilable (Type? = Type | Nil).
    Nil Safety: Use if let, ?., || default, try(&.method). Avoid not_nil! unless certain.
    State: Avoid $global. Use @@class_var (carefully) or CONSTANT. Prefer dependency injection.
    JSON: Known structures => JSON.mapping/JSON::Serializable. Dynamic => JSON::Any + early as_x? unwrapping.
    Namespacing: Use module to prevent conflicts.
    Errors: rescue SpecificError. Use stdlib types (IO::Error). Define custom errors MyError < Exception.
    Logging: Use standard Log module. Configure via Log.builder.bind.
    Testing: Use before/after_each for isolation. Fresh objects per test. Design for mocking (interfaces/modules).
    Stdlib: Use Crystal constants (STDOUT), not Ruby-isms ($stdout).
    Types (Params/Vars): Always declare. Use Type? if nil is possible.
    Tuples vs Arrays: Tuples fixed/immutable, Arrays dynamic/mutable. Use .to_a to convert Tuple->Array for flexibility.
    Hashes: Prefer literal {"k" => v} (infers type). Use {} of K => V for empty typed hash.