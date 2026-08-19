public interface IMessageFormatter
{
    string Format(string value);
}

public sealed class StandardMessageFormatter : IMessageFormatter
{
    public string Format(string value) => $"Message: {value.Trim()}";
}

public abstract class MessageFormatterFactory
{
    public abstract IMessageFormatter Create();
}

public sealed class StandardMessageFormatterFactory : MessageFormatterFactory
{
    public override IMessageFormatter Create() => new StandardMessageFormatter();
}

public static class FormatterRegistry
{
    private static readonly IReadOnlyDictionary<string, MessageFormatterFactory> Factories =
        new Dictionary<string, MessageFormatterFactory> { ["standard"] = new StandardMessageFormatterFactory() };

    public static IMessageFormatter Resolve(string mode) => Factories[mode].Create();
}

public static class MessageFormatting
{
    public static string FormatMessage(string value) => FormatterRegistry.Resolve("standard").Format(value);
}
