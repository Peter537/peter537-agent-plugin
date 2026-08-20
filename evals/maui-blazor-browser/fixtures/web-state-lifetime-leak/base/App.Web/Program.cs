var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
builder.Services.AddSingleton<SharedUi.UserDraftState>();
var app = builder.Build();
app.MapRazorComponents<SharedUi.App>().AddInteractiveServerRenderMode();
app.Run();
