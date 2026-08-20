var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
var app = builder.Build();
app.MapRazorComponents<SharedUi.App>().AddInteractiveServerRenderMode();
app.Run();
