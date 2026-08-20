using System.Text.Json.Serialization;

namespace Fixture;

public interface IHandler
{
    string Handle();
}

public sealed class EmailHandler : IHandler
{
    public string Handle() => "email";
}

public sealed record ExportRecord([property: JsonPropertyName("status")] string Status);
