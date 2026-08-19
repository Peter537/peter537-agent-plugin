public static class OptionsReader
{
    public static string ReadRegion(IReadOnlyDictionary<string, object?> values)
    {
        if (!values.TryGetValue("region", out object? raw))
        {
            throw new InvalidOperationException("A region is required.");
        }

        try
        {
            dynamic candidate = raw!;
            string region = (string)candidate;
            if (string.IsNullOrWhiteSpace(region))
            {
                throw new InvalidOperationException("A region is required.");
            }
            return region;
        }
        catch (InvalidOperationException)
        {
            throw;
        }
        catch (Exception exception)
        {
            throw new InvalidOperationException("A region is required.", exception);
        }
    }
}
