% title: introduction to baka
% date: 2021-12-11
% desc: a programming language.

awhile back i had the thought that "baka" would be a funny name for a programming language. months
later, i've started working on it as a silly pet project and excuse to get into compiler design.
baka is meant to be a simple low-level language with some nice features like type safety and
compile-time code execution. currently the scope of features i'd like to include is nebulous, so
right now i'm focused on the syntax and semantics of the language, and implementing these into a
lexer and parser.

the syntax borrows heavily from Jai and Odin, mostly because i really like the uniform syntax these
languages use for variable declarations. baka's ideology borrows from these languages as well as
others like Zig. with that in mind, some examples of baka code:

```
std :: @import("std");

main :: (argc: i32, argv: []const u8) -> !void {
    std.print("hello uwu\n");
}
```

neat!
