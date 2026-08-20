var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://0.0.0.0:5088");
builder.Services.AddSingleton<ProductionCustomerStore>();
builder.Services.AddSingleton<ProductionEmailSender>();

var app = builder.Build();
app.MapGet("/customers", (ProductionCustomerStore customers) => customers.ReadAll());
app.MapPost("/email", (ProductionEmailSender email) => email.SendPending());
app.Run();

sealed class ProductionCustomerStore
{
    public string[] ReadAll() => ["records supplied by the production profile"];
}

sealed class ProductionEmailSender
{
    public string SendPending() => "side effect requested";
}
