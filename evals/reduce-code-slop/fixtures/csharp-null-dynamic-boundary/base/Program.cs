static void Assert(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

Assert(OptionsReader.ReadRegion(new Dictionary<string, object?> { ["region"] = "eu-west" }) == "eu-west", "valid region");
foreach (var values in new IReadOnlyDictionary<string, object?>[]
{
    new Dictionary<string, object?>(),
    new Dictionary<string, object?> { ["region"] = null },
    new Dictionary<string, object?> { ["region"] = "" },
    new Dictionary<string, object?> { ["region"] = 17 },
})
{
    try
    {
        OptionsReader.ReadRegion(values);
        throw new InvalidOperationException("invalid value was accepted");
    }
    catch (InvalidOperationException exception) when (exception.Message == "A region is required.")
    {
    }
}
Console.WriteLine("fixture passed");
