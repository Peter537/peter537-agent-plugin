FROM mcr.microsoft.com/dotnet/aspnet:10.0
COPY .dev-browser-harness/bin/Release/net10.0/publish/ /app/
ENTRYPOINT ["dotnet", "/app/Harness.dll"]
