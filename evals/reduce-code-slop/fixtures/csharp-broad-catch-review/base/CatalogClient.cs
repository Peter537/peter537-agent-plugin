using System.Text.Json;

public sealed class CatalogClient(Func<CancellationToken, Task<string>> request)
{
    public async Task<IReadOnlyList<string>> FetchAsync(CancellationToken cancellationToken)
    {
        try
        {
            string payload = await request(cancellationToken);
            return JsonSerializer.Deserialize<string[]>(payload) ?? [];
        }
        catch (Exception)
        {
            return [];
        }
    }
}
