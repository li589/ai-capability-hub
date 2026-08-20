# Node.js / TypeScript Stack Reference

## Key Conventions

- Always use TypeScript with `strict: true`. No `any` unless truly unavoidable
  (and document why).
- Prefer `async/await` over callbacks or raw promises.
- Use Zod or Joi for runtime validation at API boundaries.
- Structure: controllers → services → repositories. Keep business logic in
  services, not controllers.
- Error handling: Custom error classes extending a base `AppError`. Global
  error handler middleware. Never swallow errors silently.
- Use Prisma or TypeORM for database access. Raw SQL only for complex queries
  that ORMs handle poorly.
- Logging: structured JSON logs (pino or winston). Include correlation IDs.

---

## Project Structure (NestJS)

```
src/
├── main.ts
├── app.module.ts
├── common/
│   ├── decorators/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   ├── pipes/
│   └── types/
├── config/
│   ├── config.module.ts
│   └── database.config.ts
├── modules/
│   └── users/
│       ├── users.module.ts
│       ├── users.controller.ts
│       ├── users.service.ts
│       ├── users.repository.ts
│       ├── dto/
│       │   ├── create-user.dto.ts
│       │   └── update-user.dto.ts
│       ├── entities/
│       │   └── user.entity.ts
│       └── __tests__/
│           ├── users.controller.spec.ts
│           └── users.service.spec.ts
├── database/
│   └── migrations/
└── prisma/
    └── schema.prisma
```

## Project Structure (Express / Fastify)

```
src/
├── index.ts
├── app.ts
├── config/
│   ├── index.ts
│   └── database.ts
├── middleware/
│   ├── auth.ts
│   ├── error-handler.ts
│   ├── rate-limit.ts
│   └── validate.ts
├── routes/
│   ├── index.ts
│   └── users.routes.ts
├── controllers/
│   └── users.controller.ts
├── services/
│   └── users.service.ts
├── repositories/
│   └── users.repository.ts
├── models/
│   └── user.model.ts
├── schemas/
│   └── user.schema.ts
├── types/
│   └── index.ts
├── utils/
│   ├── logger.ts
│   └── errors.ts
└── __tests__/
```

---

## Error Handling Pattern

```typescript
// Base error class
export class AppError extends Error {
  constructor(
    public readonly message: string,
    public readonly statusCode: number,
    public readonly code: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} with id ${id} not found`, 404, 'NOT_FOUND');
  }
}

export class ValidationError extends AppError {
  constructor(details: Record<string, unknown>) {
    super('Validation failed', 400, 'VALIDATION_ERROR', details);
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Authentication required') {
    super(message, 401, 'UNAUTHORIZED');
  }
}

// Global error handler middleware (Express)
export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction,
): void {
  if (err instanceof AppError) {
    res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        ...(err.details && { details: err.details }),
      },
    });
    return;
  }

  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    path: req.path,
    method: req.method,
  });

  res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
  });
}
```

---

## Validation with Zod

```typescript
import { z } from 'zod';

export const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['admin', 'user', 'moderator']).default('user'),
  metadata: z.record(z.unknown()).optional(),
});

export type CreateUserDto = z.infer<typeof CreateUserSchema>;

// Middleware factory
export function validate(schema: z.ZodSchema) {
  return (req: Request, _res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      throw new ValidationError(
        Object.fromEntries(
          result.error.issues.map((i) => [i.path.join('.'), i.message]),
        ),
      );
    }
    req.body = result.data;
    next();
  };
}
```

---

## Testing Patterns

```typescript
// Service test with mocked repository
describe('UsersService', () => {
  let service: UsersService;
  let repository: jest.Mocked<UsersRepository>;

  beforeEach(() => {
    repository = {
      findById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
    } as any;
    service = new UsersService(repository);
  });

  describe('findById', () => {
    it('returns user when found', async () => {
      const user = { id: '1', email: 'a@b.com', name: 'Test' };
      repository.findById.mockResolvedValue(user);

      const result = await service.findById('1');
      expect(result).toEqual(user);
      expect(repository.findById).toHaveBeenCalledWith('1');
    });

    it('throws NotFoundError when user missing', async () => {
      repository.findById.mockResolvedValue(null);

      await expect(service.findById('999'))
        .rejects.toThrow(NotFoundError);
    });
  });
});
```

---

## Database (Prisma Patterns)

```typescript
// Transaction example
async function createOrderWithItems(
  data: CreateOrderDto,
): Promise<Order> {
  return prisma.$transaction(async (tx) => {
    const order = await tx.order.create({
      data: {
        userId: data.userId,
        status: 'PENDING',
        total: data.items.reduce(
          (sum, item) => sum + item.price * item.quantity, 0
        ),
      },
    });

    await tx.orderItem.createMany({
      data: data.items.map((item) => ({
        orderId: order.id,
        productId: item.productId,
        quantity: item.quantity,
        unitPrice: item.price,
      })),
    });

    // Decrement stock with optimistic locking
    for (const item of data.items) {
      const updated = await tx.product.updateMany({
        where: {
          id: item.productId,
          stock: { gte: item.quantity },
        },
        data: {
          stock: { decrement: item.quantity },
        },
      });

      if (updated.count === 0) {
        throw new AppError(
          `Insufficient stock for product ${item.productId}`,
          409, 'INSUFFICIENT_STOCK',
        );
      }
    }

    return order;
  });
}
```
