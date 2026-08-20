# Async/Await Code Examples (POCU)

## Table of Contents
1. [Basic Examples](#basic-examples)
2. [Parallel Execution](#parallel-execution)
3. [Error Handling](#error-handling)
4. [Timeout Patterns](#timeout-patterns)
5. [Progress Reporting](#progress-reporting)
6. [Advanced Patterns](#advanced-patterns)

## Basic Examples

### Simple Async Operation

```csharp
public class DataFetcher
{
    private readonly ILogger mLogger;

    // ✅ POCU: Async 접미사 없음, using 문 사용
    public async Task<string> FetchData()
    {
        using (HttpClient client = new HttpClient())
        {
            string result = await client.GetStringAsync("https://api.example.com/data");
            return result;
        }
    }
}
```

### With Cancellation

```csharp
public class CancellableDataFetcher
{
    private readonly ILogger mLogger;

    // ✅ POCU: CancellationToken 지원
    public async Task<string> FetchData(CancellationToken ct)
    {
        using (HttpClient client = new HttpClient())
        {
            HttpResponseMessage response = await client.GetAsync("https://api.example.com/data", ct);
            response.EnsureSuccessStatusCode();
            string content = await response.Content.ReadAsStringAsync();
            return content;
        }
    }
}
```

## Parallel Execution

### Multiple Independent Operations

```csharp
public class DashboardService
{
    private readonly IUserRepository mUserRepository;
    private readonly IOrderRepository mOrderRepository;
    private readonly IStatsRepository mStatsRepository;

    // ✅ POCU: 명시적 타입 사용
    public async Task<Summary> GetDashboardData()
    {
        Task<List<User>> usersTask = mUserRepository.GetAll();
        Task<List<Order>> ordersTask = mOrderRepository.GetAll();
        Task<Stats> statsTask = mStatsRepository.GetCurrent();

        await Task.WhenAll(usersTask, ordersTask, statsTask);

        Summary summary = new Summary(
            await usersTask,
            await ordersTask,
            await statsTask);

        return summary;
    }
}
```

### Bounded Parallelism

```csharp
public class BatchProcessor
{
    private readonly IItemProcessor mProcessor;
    private readonly ILogger mLogger;

    // ✅ POCU: using 문 사용, 명시적 타입
    public async Task ProcessItems(List<Item> items, int maxConcurrency = 5)
    {
        Debug.Assert(items != null);
        Debug.Assert(maxConcurrency > 0);

        using (SemaphoreSlim semaphore = new SemaphoreSlim(maxConcurrency))
        {
            List<Task> tasks = new List<Task>();

            foreach (Item item in items)
            {
                await semaphore.WaitAsync();

                Task task = processItemWithSemaphore(item, semaphore);
                tasks.Add(task);
            }

            await Task.WhenAll(tasks);
        }
    }

    private async Task processItemWithSemaphore(Item item, SemaphoreSlim semaphore)
    {
        try
        {
            await mProcessor.Process(item);
        }
        finally
        {
            semaphore.Release();
        }
    }
}
```

## Error Handling

### Try-Catch with Specific Exceptions

```csharp
public class ResilientDataLoader
{
    private readonly IDataFetcher mFetcher;
    private readonly ILogger mLogger;

    private const int MAX_ATTEMPTS = 3;

    // ✅ POCU: 명시적 타입, 상수 ALL_CAPS
    public async Task<Data> LoadDataWithRetry(CancellationToken ct)
    {
        int attempts = 0;

        while (attempts < MAX_ATTEMPTS)
        {
            try
            {
                Data data = await mFetcher.Fetch(ct);
                return data;
            }
            catch (HttpRequestException ex) when (attempts < MAX_ATTEMPTS - 1)
            {
                attempts++;
                mLogger.Warning($"Attempt {attempts} failed: {ex.Message}");

                int delaySeconds = (int)Math.Pow(2, attempts);
                await Task.Delay(TimeSpan.FromSeconds(delaySeconds), ct);
            }
            catch (OperationCanceledException)
            {
                mLogger.Info("Operation cancelled");
                throw;
            }
        }

        throw new InvalidOperationException("Max retry attempts exceeded");
    }
}
```

### Exception Aggregation

```csharp
public class ParallelProcessor
{
    private readonly IItemProcessor mProcessor;

    // ✅ POCU: 명시적 타입
    public async Task ProcessAll(List<Item> items)
    {
        Debug.Assert(items != null);

        List<Task> tasks = new List<Task>();
        foreach (Item item in items)
        {
            Task task = mProcessor.Process(item);
            tasks.Add(task);
        }

        try
        {
            await Task.WhenAll(tasks);
        }
        catch
        {
            // Collect all exceptions
            List<AggregateException> exceptions = new List<AggregateException>();
            foreach (Task task in tasks)
            {
                if (task.IsFaulted && task.Exception != null)
                {
                    exceptions.Add(task.Exception);
                }
            }

            if (exceptions.Count > 0)
            {
                throw new AggregateException(exceptions);
            }
        }
    }
}
```

## Timeout Patterns

### Using CancellationTokenSource

```csharp
public class TimeoutLoader
{
    private readonly IDataLoader mLoader;
    private readonly ILogger mLogger;

    // ✅ POCU: using 문 사용
    public async Task<Data> LoadWithTimeout(TimeSpan timeout)
    {
        using (CancellationTokenSource cts = new CancellationTokenSource(timeout))
        {
            try
            {
                Data data = await mLoader.Load(cts.Token);
                return data;
            }
            catch (OperationCanceledException) when (cts.IsCancellationRequested)
            {
                throw new TimeoutException($"Operation exceeded {timeout}");
            }
        }
    }
}
```

### Using Task.WhenAny

```csharp
public class WhenAnyTimeoutLoader
{
    private readonly IDataLoader mLoader;

    // ✅ POCU: 명시적 타입
    public async Task<Data> LoadWithTimeout(TimeSpan timeout)
    {
        Task<Data> dataTask = mLoader.Load();
        Task timeoutTask = Task.Delay(timeout);

        Task completed = await Task.WhenAny(dataTask, timeoutTask);

        if (completed == timeoutTask)
        {
            throw new TimeoutException($"Operation exceeded {timeout}");
        }

        Data data = await dataTask;
        return data;
    }
}
```

## Progress Reporting

### IProgress<T> Pattern

```csharp
public class ProgressiveProcessor
{
    private readonly IItemLoader mLoader;
    private readonly IItemProcessor mProcessor;

    // ✅ POCU: IProgress<T> 패턴
    public async Task<Summary> ProcessWithProgress(
        IProgress<int> progressOrNull,
        CancellationToken ct)
    {
        List<Item> items = await mLoader.Load(ct);
        int total = items.Count;

        Debug.Assert(total > 0);

        for (int i = 0; i < total; i++)
        {
            ct.ThrowIfCancellationRequested();

            await mProcessor.Process(items[i], ct);

            // Report progress percentage
            if (progressOrNull != null)
            {
                int percent = (i + 1) * 100 / total;
                progressOrNull.Report(percent);
            }
        }

        Summary summary = createSummary(items);
        return summary;
    }

    private Summary createSummary(List<Item> items)
    {
        Debug.Assert(items != null);
        return new Summary(items);
    }
}

// Usage
public class ProgressConsumer
{
    private readonly ProgressiveProcessor mProcessor;
    private readonly ILogger mLogger;

    public async Task Execute()
    {
        Progress<int> progress = new Progress<int>(percent =>
        {
            mLogger.Info($"Progress: {percent}%");
        });

        Summary summary = await mProcessor.ProcessWithProgress(progress, CancellationToken.None);
    }
}
```

## Advanced Patterns

### Lazy Async Initialization

```csharp
// ✅ POCU: mPascalCase for private fields
public class AsyncLazy<T>
{
    private readonly Lazy<Task<T>> mInstance;

    public AsyncLazy(Func<Task<T>> factory)
    {
        Debug.Assert(factory != null);
        mInstance = new Lazy<Task<T>>(factory);
    }

    public Task<T> Value => mInstance.Value;
}

// Usage
public class ConfigService
{
    private readonly AsyncLazy<Config> mConfig;
    private readonly IConfigLoader mLoader;

    public ConfigService(IConfigLoader loader)
    {
        mLoader = loader;
        mConfig = new AsyncLazy<Config>(() => mLoader.Load());
    }

    public async Task UseConfig()
    {
        Config config = await mConfig.Value; // Loads once, reuses thereafter
        applyConfig(config);
    }

    private void applyConfig(Config config)
    {
        Debug.Assert(config != null);
        // Apply configuration
    }
}
```

### Async Semaphore

```csharp
// ✅ POCU: mPascalCase, camelCase for private methods
public class AsyncResource
{
    private readonly SemaphoreSlim mSemaphore;

    public AsyncResource()
    {
        mSemaphore = new SemaphoreSlim(1, 1);
    }

    public async Task<T> Execute<T>(Func<Task<T>> operation)
    {
        Debug.Assert(operation != null);

        await mSemaphore.WaitAsync();
        try
        {
            T result = await operation();
            return result;
        }
        finally
        {
            mSemaphore.Release();
        }
    }
}
```

### Async Event

```csharp
// ✅ POCU: mPascalCase for private fields
public class AsyncEventHandler
{
    private readonly List<Func<Task>> mHandlers;

    public AsyncEventHandler()
    {
        mHandlers = new List<Func<Task>>();
    }

    public void Subscribe(Func<Task> handler)
    {
        Debug.Assert(handler != null);
        mHandlers.Add(handler);
    }

    public void Unsubscribe(Func<Task> handler)
    {
        Debug.Assert(handler != null);
        mHandlers.Remove(handler);
    }

    public async Task Raise()
    {
        List<Task> tasks = new List<Task>();
        foreach (Func<Task> handler in mHandlers)
        {
            Task task = handler();
            tasks.Add(task);
        }

        await Task.WhenAll(tasks);
    }
}
```
