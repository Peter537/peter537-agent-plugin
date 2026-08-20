using System.Reflection;
using System.Text.Json;

var handlerType = Assembly.GetExecutingAssembly().GetType("Fixture.EmailHandler", throwOnError: true)!;
var handler = (Fixture.IHandler)Activator.CreateInstance(handlerType)!;
Console.WriteLine(handler.Handle());
Console.WriteLine(JsonSerializer.Serialize(new Fixture.ExportRecord("ready")));
