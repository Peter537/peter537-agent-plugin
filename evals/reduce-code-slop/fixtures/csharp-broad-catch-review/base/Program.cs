static void Assert(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

var success = new CatalogClient(_ => Task.FromResult("[\"alpha\"]"));
Assert((await success.FetchAsync(CancellationToken.None)).SequenceEqual(["alpha"]), "successful response");

var failure = new CatalogClient(_ => Task.FromException<string>(new TimeoutException("fixture timeout")));
Assert((await failure.FetchAsync(CancellationToken.None)).Count == 0, "current failure behavior");

var cancellation = new CatalogClient(token => Task.FromCanceled<string>(token));
using var source = new CancellationTokenSource();
source.Cancel();
Assert((await cancellation.FetchAsync(source.Token)).Count == 0, "current cancellation behavior");
Console.WriteLine("fixture passed");
