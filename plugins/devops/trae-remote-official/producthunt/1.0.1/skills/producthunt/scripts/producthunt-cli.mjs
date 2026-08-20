#!/usr/bin/env node

/**
 * Product Hunt CLI — GraphQL API client using Developer Token
 *
 * Usage:
 *   node producthunt-cli.mjs <command> [options]
 *
 * Environment:
 *   PRODUCTHUNT_TOKEN — Developer Token (required)
 *
 * Commands:
 *   posts        — Query products (options: --topic, --order, --first, --after, --before-date, --after-date, --featured)
 *   post         — Get product details (options: --slug or --id)
 *   topics       — Query topics (options: --query, --order, --first)
 *   topic        — Get topic details (options: --slug or --id)
 *   collections  — Query collections (options: --featured, --order, --first)
 *   collection   — Get collection details (options: --slug or --id)
 *   user         — Get user info (options: --username or --id)
 *   viewer       — Get current authenticated user info
 */

const GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql";

function getToken() {
  const token = process.env.PRODUCTHUNT_TOKEN;
  if (!token) {
    console.error("Error: PRODUCTHUNT_TOKEN environment variable is required.");
    process.exit(1);
  }
  return token;
}

async function graphql(query, variables) {
  const token = getToken();
  const body = { query };
  if (variables) body.variables = variables;

  const res = await fetch(GRAPHQL_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error(`HTTP ${res.status}: ${text}`);
    process.exit(1);
  }

  const json = await res.json();
  if (json.errors) {
    console.error("GraphQL errors:");
    console.error(JSON.stringify(json.errors, null, 2));
    process.exit(1);
  }
  return json.data;
}

function parseArgs(args) {
  const opts = {};
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg.startsWith("--")) {
      const key = arg.slice(2);
      const next = args[i + 1];
      if (next && !next.startsWith("--")) {
        opts[key] = next;
        i++;
      } else {
        opts[key] = "true";
      }
    }
  }
  return opts;
}

function output(data) {
  console.log(JSON.stringify(data, null, 2));
}

async function cmdPosts(opts) {
  const first = parseInt(opts.first) || 10;
  const order = (opts.order || "VOTES").toUpperCase();
  const topic = opts.topic || null;
  const featured = opts.featured === "true" ? true : null;
  const postedAfter = opts["after-date"] || null;
  const postedBefore = opts["before-date"] || null;
  const after = opts.after || null;

  const args = [];
  args.push(`first: ${first}`);
  args.push(`order: ${order}`);
  if (topic) args.push(`topic: "${topic}"`);
  if (featured !== null) args.push(`featured: ${featured}`);
  if (postedAfter) args.push(`postedAfter: "${postedAfter}"`);
  if (postedBefore) args.push(`postedBefore: "${postedBefore}"`);
  if (after) args.push(`after: "${after}"`);

  const query = `{
    posts(${args.join(", ")}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id name tagline slug votesCount commentsCount
          url website createdAt featuredAt
          dailyRank weeklyRank
          topics(first: 3) { edges { node { name slug } } }
          makers { name username }
        }
      }
    }
  }`;

  const data = await graphql(query);
  output(data.posts);
}

async function cmdPost(opts) {
  const slug = opts.slug;
  const id = opts.id;
  if (!slug && !id) {
    console.error("Error: --slug or --id is required");
    process.exit(1);
  }

  const arg = slug ? `slug: "${slug}"` : `id: "${id}"`;
  const query = `{
    post(${arg}) {
      id name tagline slug description
      votesCount commentsCount reviewsCount reviewsRating
      dailyRank weeklyRank monthlyRank
      url website createdAt featuredAt
      isVoted isCollected
      user { name username }
      makers { name username headline }
      topics(first: 5) { edges { node { name slug } } }
      media { type url videoUrl }
      productLinks { type url }
      comments(first: 5, order: VOTES_COUNT) {
        edges { node { body votesCount user { name username } createdAt } }
      }
    }
  }`;

  const data = await graphql(query);
  output(data.post);
}

async function cmdTopics(opts) {
  const first = parseInt(opts.first) || 10;
  const order = (opts.order || "FOLLOWERS_COUNT").toUpperCase();
  const queryStr = opts.query || null;

  const args = [`first: ${first}`, `order: ${order}`];
  if (queryStr) args.push(`query: "${queryStr}"`);

  const query = `{
    topics(${args.join(", ")}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node { id name slug description postsCount followersCount }
      }
    }
  }`;

  const data = await graphql(query);
  output(data.topics);
}

async function cmdTopic(opts) {
  const slug = opts.slug;
  const id = opts.id;
  if (!slug && !id) {
    console.error("Error: --slug or --id is required");
    process.exit(1);
  }

  const arg = slug ? `slug: "${slug}"` : `id: "${id}"`;
  const query = `{
    topic(${arg}) {
      id name slug description url postsCount followersCount isFollowing createdAt
    }
  }`;

  const data = await graphql(query);
  output(data.topic);
}

async function cmdCollections(opts) {
  const first = parseInt(opts.first) || 10;
  const order = (opts.order || "FOLLOWERS_COUNT").toUpperCase();
  const featured = opts.featured === "true" ? true : null;

  const args = [`first: ${first}`, `order: ${order}`];
  if (featured !== null) args.push(`featured: ${featured}`);

  const query = `{
    collections(${args.join(", ")}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      edges {
        node {
          id name tagline description url followersCount createdAt
          user { name username }
          posts(first: 3) { edges { node { name votesCount } } }
        }
      }
    }
  }`;

  const data = await graphql(query);
  output(data.collections);
}

async function cmdCollection(opts) {
  const slug = opts.slug;
  const id = opts.id;
  if (!slug && !id) {
    console.error("Error: --slug or --id is required");
    process.exit(1);
  }

  const arg = slug ? `slug: "${slug}"` : `id: "${id}"`;
  const query = `{
    collection(${arg}) {
      id name tagline description url followersCount createdAt featuredAt
      user { name username }
      posts(first: 10) {
        edges { node { name tagline votesCount url } }
      }
      topics(first: 5) { edges { node { name slug } } }
    }
  }`;

  const data = await graphql(query);
  output(data.collection);
}

async function cmdUser(opts) {
  const username = opts.username;
  const id = opts.id;
  if (!username && !id) {
    console.error("Error: --username or --id is required");
    process.exit(1);
  }

  const arg = username ? `username: "${username}"` : `id: "${id}"`;
  const query = `{
    user(${arg}) {
      id name username headline url websiteUrl
      twitterUsername profileImage
      followersCount followingCount isMaker createdAt
      madePosts(first: 5) { edges { node { name tagline votesCount url } } }
      submittedPosts(first: 5) { edges { node { name tagline votesCount url } } }
    }
  }`;

  const data = await graphql(query);
  output(data.user);
}

async function cmdViewer() {
  const query = `{
    viewer {
      user {
        id name username headline url
        followersCount followingCount isMaker createdAt
        votedPosts(first: 5) { edges { node { name tagline votesCount } } }
        submittedPosts(first: 5) { edges { node { name tagline votesCount url } } }
      }
    }
  }`;

  const data = await graphql(query);
  output(data.viewer);
}

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  const opts = parseArgs(args.slice(1));

  switch (command) {
    case "posts":
      await cmdPosts(opts);
      break;
    case "post":
      await cmdPost(opts);
      break;
    case "topics":
      await cmdTopics(opts);
      break;
    case "topic":
      await cmdTopic(opts);
      break;
    case "collections":
      await cmdCollections(opts);
      break;
    case "collection":
      await cmdCollection(opts);
      break;
    case "user":
      await cmdUser(opts);
      break;
    case "viewer":
      await cmdViewer();
      break;
    default:
      console.error(`Product Hunt CLI

Usage: node producthunt-cli.mjs <command> [options]

Commands:
  posts         Query products list
  post          Get single product details
  topics        Query topics list
  topic         Get single topic details
  collections   Query collections list
  collection    Get single collection details
  user          Get user profile
  viewer        Get current authenticated user

Global Options:
  --first <n>        Number of results (default: 10)
  --order <ORDER>    Sort order (varies by command)

posts Options:
  --topic <slug>     Filter by topic slug (e.g. "artificial-intelligence")
  --order <ORDER>    VOTES | NEWEST | RANKING | FEATURED_AT (default: VOTES)
  --featured         Only featured posts
  --after-date <dt>  Posts after this date (ISO-8601)
  --before-date <dt> Posts before this date (ISO-8601)
  --after <cursor>   Pagination cursor

post Options:
  --slug <slug>      Product slug
  --id <id>          Product ID

topics Options:
  --query <text>     Search topics by keyword
  --order <ORDER>    FOLLOWERS_COUNT | NEWEST (default: FOLLOWERS_COUNT)

topic Options:
  --slug <slug>      Topic slug
  --id <id>          Topic ID

collections Options:
  --featured         Only featured collections
  --order <ORDER>    FOLLOWERS_COUNT | NEWEST | FEATURED_AT (default: FOLLOWERS_COUNT)

collection Options:
  --slug <slug>      Collection slug
  --id <id>          Collection ID

user Options:
  --username <name>  Username
  --id <id>          User ID

Environment Variables:
  PRODUCTHUNT_TOKEN  Developer Token (required)
`);
      process.exit(command ? 1 : 0);
  }
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
