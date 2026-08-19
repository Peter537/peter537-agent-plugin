if (Message.Normalize(" ready ") != "ready")
{
    throw new InvalidOperationException("message normalization failed");
}
Console.WriteLine("fixture passed");
