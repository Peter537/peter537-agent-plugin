var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorComponents();
var app = builder.Build();
app.MapRazorComponents<SharedUi.App>();
app.Run();
