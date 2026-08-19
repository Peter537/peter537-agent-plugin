public static class Message
{
    public static string Normalize(string value)
    {
        ArgumentNullException.ThrowIfNull(value);
        return value.Trim();
    }
}
