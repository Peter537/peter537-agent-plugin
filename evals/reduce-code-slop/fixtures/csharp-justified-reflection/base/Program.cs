var handlers = HandlerLoader.Load(typeof(ExampleHandler).Assembly);
if (handlers.Count != 1 || handlers[0].Name != "example")
{
    throw new InvalidOperationException("handler discovery failed");
}
Console.WriteLine("fixture passed");
