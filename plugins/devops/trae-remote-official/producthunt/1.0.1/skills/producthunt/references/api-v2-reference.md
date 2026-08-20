# Product Hunt API V2 Reference

> GraphQL endpoint: `https://api.producthunt.com/v2/api/graphql`
> Auth header: `Authorization: Bearer {developer_token}`

---

## Queries

```graphql
post(id: ID, slug: String): Post
posts(featured: Boolean, postedBefore: DateTime, postedAfter: DateTime, topic: String, order: PostsOrder, twitterUrl: String, url: String, after: String, before: String, first: Int, last: Int): PostConnection!
topic(id: ID, slug: String): Topic
topics(followedByUserid: ID, query: String, order: TopicsOrder, after: String, before: String, first: Int, last: Int): TopicConnection!
collection(id: ID, slug: String): Collection
collections(postId: ID, userId: ID, featured: Boolean, order: CollectionsOrder, after: String, before: String, first: Int, last: Int): CollectionConnection!
comment(id: ID!): Comment
user(id: ID, username: String): User
viewer: Viewer
```

---

## Mutations

> Require `write` scope and user-context token.

```graphql
userFollow(input: UserFollowInput!): UserFollowPayload
userFollowUndo(input: UserFollowUndoInput!): UserFollowUndoPayload
```

Input fields: `{ id: ID!, clientMutationId: String }`. Payload: `{ node: User, errors: [Error!]! }`.

---

## Types

### Post

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Product ID |
| `name` | String! | Product name |
| `tagline` | String! | Product tagline |
| `slug` | String! | URL-friendly slug |
| `description` | String | Plain text description |
| `url` | String! | PH product URL |
| `website` | String! | Redirect to product's official site |
| `votesCount` | Int! | Weighted vote score |
| `commentsCount` | Int! | Comment count |
| `reviewsCount` | Int! | Review count |
| `reviewsRating` | Float! | Aggregate rating |
| `makerReplies` | Int! | Maker reply count |
| `dailyRank` | Int | Daily rank |
| `weeklyRank` | Int | Weekly rank |
| `monthlyRank` | Int | Monthly rank |
| `yearlyRank` | Int | Yearly rank |
| `createdAt` | DateTime! | Creation time |
| `featuredAt` | DateTime | Featured time |
| `isVoted` | Boolean! | Current user voted? |
| `isCollected` | Boolean! | Current user collected? |
| `user` | User! | Poster |
| `makers` | [User!]! | Makers list |
| `media` | [Media!]! | Media resources |
| `thumbnail` | Media | Thumbnail |
| `productLinks` | [ProductLink!]! | Additional links |
| `topics` | TopicConnection! | Associated topics |
| `collections` | CollectionConnection! | Containing collections |
| `comments` | CommentConnection! | Comments (supports `order: CommentsOrder`) |
| `votes` | VoteConnection! | Votes (supports `createdAfter`/`createdBefore`) |

### User

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | User ID |
| `name` | String! | Display name |
| `username` | String! | Username |
| `headline` | String | Bio/headline |
| `url` | String! | Profile URL |
| `websiteUrl` | String | Website URL |
| `profileImage` | String | Avatar URL (supports `size: Int`) |
| `twitterUsername` | String | Twitter handle |
| `createdAt` | DateTime | Registration time |
| `followersCount` | Int! | Follower count |
| `followingCount` | Int! | Following count |
| `isMaker` | Boolean! | Certified Maker? |
| `isFollowing` | Boolean! | Current user following? |
| `madePosts` | PostConnection! | Products made |
| `submittedPosts` | PostConnection! | Submitted products |
| `votedPosts` | PostConnection! | Voted products |

### Topic

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Topic ID |
| `name` | String! | Name |
| `slug` | String! | URL slug |
| `description` | String! | Description |
| `url` | String! | Public URL |
| `postsCount` | Int! | Product count |
| `followersCount` | Int! | Follower count |
| `isFollowing` | Boolean! | Current user following? |
| `createdAt` | DateTime! | Creation time |

### Collection

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Collection ID |
| `name` | String! | Name |
| `tagline` | String! | Tagline |
| `description` | String | Description |
| `url` | String! | Public URL |
| `followersCount` | Int! | Follower count |
| `isFollowing` | Boolean! | Current user following? |
| `createdAt` | DateTime! | Creation time |
| `featuredAt` | DateTime | Featured time |
| `user` | User! | Creator |
| `posts` | PostConnection! | Products in collection |
| `topics` | TopicConnection! | Associated topics |

### Comment

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID! | Comment ID |
| `body` | String! | Content (HTML) |
| `url` | String! | Public URL |
| `createdAt` | DateTime! | Creation time |
| `votesCount` | Int! | Vote count |
| `isVoted` | Boolean! | Current user voted? |
| `user` | User! | Author |
| `parent` | Comment | Parent (null if top-level) |
| `replies` | CommentConnection! | Replies |

### Media

| Field | Type | Description |
|-------|------|-------------|
| `type` | String! | Media type |
| `url` | String! | Public URL (supports `width`/`height`) |
| `videoUrl` | String | Video URL |

### Viewer

`{ user: User! }` — Current authenticated user.

### Vote

`{ id: ID!, createdAt: DateTime!, user: User!, userId: ID! }`

### ProductLink

`{ type: String!, url: String! }`

### Error

`{ field: String!, message: String! }`

---

## Enums

| Enum | Values |
|------|--------|
| PostsOrder | `FEATURED_AT`, `VOTES`, `RANKING`, `NEWEST` |
| CollectionsOrder | `NEWEST`, `FOLLOWERS_COUNT`, `FEATURED_AT` |
| TopicsOrder | `NEWEST`, `FOLLOWERS_COUNT` |
| CommentsOrder | `NEWEST`, `VOTES_COUNT` |

---

## Pagination (Relay Connection)

All list queries support: `first`, `last`, `after`, `before`.

Each Connection returns:
- `edges[].cursor` / `edges[].node` — Items with cursors
- `nodes` — Direct node list
- `pageInfo { hasNextPage, hasPreviousPage, startCursor, endCursor }`
- `totalCount`

---

## Scalar Types

| Type | Description |
|------|-------------|
| `ID` | Base64-encoded identifier (also accepts integers) |
| `DateTime` | ISO-8601 UTC string (e.g. `"2026-07-19T00:00:00Z"`) |
