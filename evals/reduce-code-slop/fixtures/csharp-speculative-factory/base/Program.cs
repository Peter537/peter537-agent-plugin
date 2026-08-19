if (MessageFormatting.FormatMessage(" ready ") != "Message: ready")
{
    throw new InvalidOperationException("formatter output changed");
}
Console.WriteLine("fixture passed");
