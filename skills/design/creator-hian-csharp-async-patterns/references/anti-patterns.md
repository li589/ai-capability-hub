# Async Anti-Patterns (POCU)

## Table of Contents
1. [Blocking on Async Code](#1-blocking-on-async-code)
2. [Async Void (Outside Event Handlers)](#2-async-void-outside-event-handlers)
3. [Fire-and-Forget Without Error Handling](#3-fire-and-forget-without-error-handling)
4. [Missing Cancellation Support](#4-missing-cancellation-support)
5. [Over-Using Async](#5-over-using-async)
6. [Not Passing CancellationToken Through](#6-not-passing-cancellationtoken-through)
7. [Capturing Modified Variables in Async Loops](#7-capturing-modified-variables-in-async-loops)
8. [Async in Constructors](#8-async-in-constructors)
9. [Ignoring Task Results](#9-ignoring-task-results)
10. [Mixing Sync and Async Code Poorly](#10-mixing-sync-and-async-code-poorly)

## 1. Blocking on Async Code

### ❌ The Problem

```csharp
public class BadService
{
    public void SyncMethod()
    {
        // DEADLOCK RISK!
        Result result = DoWork().Result;
        Result result2 = DoWork().GetAwaiter().GetResult();
        DoWork().Wait();
    }
}
```

**Why it's bad**: Can cause deadlocks, especially in UI applications with synchronization context.

### ✅ The Solution (POCU)

```csharp
public class GoodService
{
    private readonly ILogger mLogger;

    // ✅ POCU: Async 접미사 없음
    public async Task DoWorkProperly()
    {
        Result result = await doWork();
        process(result);
    }

    private async Task<Result> doWork()
    {
        return await mRepository.Load();
    }

    private void process(Result result)
    {
        Debug.Assert(result != null);
        // Process result
    }

    // If you must have sync entry point (not recommended):
    public void SyncEntryPoint()
    {
        doWork().GetAwaiter().GetResult(); // Use with extreme caution
    }
}
```

## 2. Async Void (Outside Event Handlers)

### ❌ The Problem

```csharp
// BAD: Exceptions are lost!
public async void LoadData()
{
    await Task.Delay(1000);
    throw new Exception("This crashes the app!");
}
```

**Why it's bad**: Exceptions cannot be caught by caller, leading to application crashes.

### ✅ The Solution (POCU)

```csharp
public class DataLoader
{
    private readonly ILogger mLogger;

    // ✅ POCU: Returns Task, Async 접미사 없음
    public async Task LoadData()
    {
        await Task.Delay(1000);
        throw new Exception("Can be caught by caller");
    }

    // ⚠️ EXCEPTION: Event handlers MUST be async void
    private async void OnButtonClick(object sender, EventArgs e)
    {
        try
        {
            await LoadData();
        }
        catch (Exception ex)
        {
            mLogger.Error(ex, "Button click failed");
        }
    }
}
```

## 3. Fire-and-Forget Without Error Handling

### ❌ The Problem

```csharp
public class BadFireAndForget
{
    public void StartOperation()
    {
        _ = LongRunning(); // Exceptions disappear!
    }
}
```

**Why it's bad**: Exceptions are silently swallowed, making debugging impossible.

### ✅ The Solution (POCU)

```csharp
public class GoodFireAndForget
{
    private readonly ILogger mLogger;

    public void StartOperation()
    {
        _ = safeFireAndForget();
    }

    // ✅ POCU: camelCase for private methods
    private async Task safeFireAndForget()
    {
        try
        {
            await longRunning();
        }
        catch (Exception ex)
        {
            mLogger.Error(ex, "Background operation failed");
            // Optionally: notify user, retry, etc.
        }
    }

    private async Task longRunning()
    {
        await Task.Delay(5000);
        // Long running work
    }
}
```

## 4. Missing Cancellation Support

### ❌ The Problem

```csharp
// BAD: No way to cancel
public async Task LongProcess()
{
    for (int i = 0; i < 1000; i++)
    {
        await ProcessItem(i);
    }
}
```

**Why it's bad**: User cannot stop long-running operations, wastes resources.

### ✅ The Solution (POCU)

```csharp
public class CancellableProcessor
{
    private readonly IItemProcessor mProcessor;

    // ✅ POCU: Cancellable
    public async Task LongProcess(CancellationToken ct)
    {
        for (int i = 0; i < 1000; i++)
        {
            ct.ThrowIfCancellationRequested();
            await mProcessor.Process(i, ct);
        }
    }
}
```

## 5. Over-Using Async

### ❌ The Problem

```csharp
// BAD: Unnecessary async overhead
public async Task<int> GetValue()
{
    return await Task.FromResult(42);
}

public async Task<string> GetName()
{
    return await Task.FromResult("John");
}
```

**Why it's bad**: Async machinery adds overhead for synchronous operations.

### ✅ The Solution (POCU)

```csharp
public class ValueProvider
{
    // ✅ POCU: Return Task directly or use sync method
    public Task<int> GetValue()
    {
        return Task.FromResult(42);
    }

    // Or better: Just use synchronous method
    public int GetValueSync()
    {
        return 42;
    }

    public string GetNameSync()
    {
        return "John";
    }
}
```

## 6. Not Passing CancellationToken Through

### ❌ The Problem

```csharp
public async Task Process(CancellationToken ct)
{
    // BAD: Not passing ct to inner calls
    await Step1();
    await Step2();
    await Step3();
}
```

**Why it's bad**: Cancellation doesn't propagate, operations continue unnecessarily.

### ✅ The Solution (POCU)

```csharp
public class ProcessorWithCancellation
{
    // ✅ POCU: Pass ct through all async calls
    public async Task Process(CancellationToken ct)
    {
        await step1(ct);
        await step2(ct);
        await step3(ct);
    }

    private async Task step1(CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        await Task.Delay(100, ct);
    }

    private async Task step2(CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        await Task.Delay(100, ct);
    }

    private async Task step3(CancellationToken ct)
    {
        ct.ThrowIfCancellationRequested();
        await Task.Delay(100, ct);
    }
}
```

## 7. Capturing Modified Variables in Async Loops

### ❌ The Problem

```csharp
// BAD: Variable capture issue
List<Task> tasks = new List<Task>();
for (int i = 0; i < 10; i++)
{
    tasks.Add(Task.Run(async () =>
    {
        await Task.Delay(100);
        Console.WriteLine(i); // All print 10!
    }));
}
```

**Why it's bad**: Loop variable is captured by reference, all tasks see final value.

### ✅ The Solution (POCU)

```csharp
public class LoopCaptureFixed
{
    private readonly ILogger mLogger;

    public async Task ExecuteLoop()
    {
        // ✅ POCU: 명시적 타입, 변수 캡처 수정
        List<Task> tasks = new List<Task>();

        for (int i = 0; i < 10; i++)
        {
            int index = i; // Copy to local variable
            Task task = Task.Run(async () =>
            {
                await Task.Delay(100);
                mLogger.Info($"Index: {index}"); // Prints 0-9
            });
            tasks.Add(task);
        }

        await Task.WhenAll(tasks);
    }
}
```

## 8. Async in Constructors

### ❌ The Problem

```csharp
// BAD: Cannot await in constructor
public class BadService
{
    public BadService()
    {
        // Cannot use async/await here!
        Initialize().Wait(); // DEADLOCK RISK
    }
}
```

**Why it's bad**: Constructors cannot be async, blocking causes deadlocks.

### ✅ The Solution (POCU)

```csharp
// ✅ POCU: Factory pattern
public class GoodService
{
    private readonly Config mConfig;

    private GoodService(Config config)
    {
        Debug.Assert(config != null);
        mConfig = config;
    }

    public static async Task<GoodService> Create()
    {
        Config config = await loadConfig();
        GoodService service = new GoodService(config);
        return service;
    }

    private static async Task<Config> loadConfig()
    {
        await Task.Delay(100);
        return new Config();
    }
}

// Or: Lazy initialization
public class LazyService
{
    private readonly Task mInitTask;
    private bool mbIsInitialized;

    public LazyService()
    {
        mInitTask = initialize();
    }

    public async Task EnsureInitialized()
    {
        await mInitTask;
    }

    private async Task initialize()
    {
        await Task.Delay(100);
        mbIsInitialized = true;
    }
}
```

## 9. Ignoring Task Results

### ❌ The Problem

```csharp
public async Task Process()
{
    Task.Run(() => BackgroundWork()); // Task ignored!
    await OtherWork();
}
```

**Why it's bad**: Background task exceptions are lost, no way to track completion.

### ✅ The Solution (POCU)

```csharp
public class TaskTracker
{
    private readonly ILogger mLogger;

    public async Task Process()
    {
        // ✅ POCU: 명시적 타입
        Task backgroundTask = Task.Run(() => backgroundWork());

        await otherWork();

        // Wait for background work
        await backgroundTask;
    }

    private void backgroundWork()
    {
        // Background operation
    }

    private async Task otherWork()
    {
        await Task.Delay(100);
    }

    // Or if truly fire-and-forget:
    public void StartBackground()
    {
        _ = safeFireAndForget();
    }

    private async Task safeFireAndForget()
    {
        try
        {
            await backgroundTask();
        }
        catch (Exception ex)
        {
            mLogger.Error(ex, "Background task failed");
        }
    }

    private async Task backgroundTask()
    {
        await Task.Delay(1000);
    }
}
```

## 10. Mixing Sync and Async Code Poorly

### ❌ The Problem

```csharp
// BAD: Mixed sync/async
public void ProcessData()
{
    Data data = LoadData().Result; // Blocking!
    SaveData(data); // Sync
}
```

**Why it's bad**: Loses benefits of async, introduces deadlock risks.

### ✅ The Solution (POCU)

```csharp
public class ConsistentProcessor
{
    private readonly IRepository mRepository;

    // ✅ POCU: Async all the way
    public async Task ProcessData()
    {
        Data data = await mRepository.Load();
        await mRepository.Save(data);
    }

    // Or: Sync all the way
    public void ProcessDataSync()
    {
        Data data = mRepository.LoadSync();
        mRepository.SaveSync(data);
    }
}
```

## Summary Checklist

Avoid these anti-patterns:

- [ ] .Result, .Wait() 차단 금지
- [ ] async void 금지 (이벤트 핸들러 제외)
- [ ] Fire-and-forget에 에러 처리 필수
- [ ] 모든 장기 작업에 CancellationToken 필수
- [ ] 호출 체인 전체에 CancellationToken 전달
- [ ] async는 진정한 I/O-bound 작업에만 사용
- [ ] 루프 변수 캡처 올바르게 처리
- [ ] 생성자에서 async 금지
- [ ] Task 결과 무시 금지
- [ ] 호출 체인 전체에서 sync 또는 async 일관성 유지
- [ ] Async 접미사 금지 (POCU 표준)
- [ ] var 대신 명시적 타입 사용
- [ ] using 선언 대신 using 문 사용
