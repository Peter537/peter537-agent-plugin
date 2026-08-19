using System.Reflection;

[AttributeUsage(AttributeTargets.Class)]
public sealed class HandlerAttribute : Attribute;

public interface IHandler
{
    string Name { get; }
}

[Handler]
public sealed class ExampleHandler : IHandler
{
    public string Name => "example";
}

[Handler]
public sealed class OpenGenericHandler<T> : IHandler
{
    public string Name => typeof(T).Name;
}

public static class HandlerLoader
{
    public static IReadOnlyList<IHandler> Load(Assembly assembly) => assembly
        .GetTypes()
        .Where(type =>
            type.GetCustomAttribute<HandlerAttribute>() is not null &&
            typeof(IHandler).IsAssignableFrom(type) &&
            !type.IsAbstract &&
            !type.ContainsGenericParameters &&
            type.GetConstructor(Type.EmptyTypes) is not null)
        .Select(type => (IHandler)Activator.CreateInstance(type)!)
        .ToArray();
}
