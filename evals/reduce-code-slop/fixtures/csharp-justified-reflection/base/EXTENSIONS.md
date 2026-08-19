# Handler extension boundary

Deployment assemblies contribute handlers at runtime. A handler opts in with `HandlerAttribute`, implements `IHandler`, and provides a public parameterless constructor. The host cannot replace this with a compile-time registry because extension assemblies are supplied independently.
