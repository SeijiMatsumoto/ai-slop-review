// AI-generated PR — review this code
// Description: Added GraphQL resolvers for users, posts, and comments with nested relations

import { PrismaClient } from "@prisma/client";
import { ApolloServer } from "@apollo/server";
import { startStandaloneServer } from "@apollo/server/standalone";

const prisma = new PrismaClient();

const typeDefs = `#graphql
  type User {
    id: ID!
    name: String!
    email: String!
    bio: String
    posts: [Post!]!
    comments: [Comment!]!
    createdAt: String!
  }

  type Post {
    id: ID!
    title: String!
    content: String!
    published: Boolean!
    author: User!
    comments: [Comment!]!
    createdAt: String!
    updatedAt: String!
  }

  type Comment {
    id: ID!
    body: String!
    author: User!
    post: Post!
    createdAt: String!
  }

  type Query {
    users(limit: Int, offset: Int): [User!]!
    user(id: ID!): User
    posts(published: Boolean, limit: Int, offset: Int): [Post!]!
    post(id: ID!): Post
    comments(postId: ID!): [Comment!]!
  }

  type Mutation {
    createUser(name: String!, email: String!, bio: String): User!
    updateUser(id: ID!, name: String, email: String, bio: String): User!
    createPost(title: String!, content: String!, authorId: ID!): Post!
    updatePost(id: ID!, title: String, content: String, published: Boolean): Post!
    deletePost(id: ID!): Boolean!
    createComment(body: String!, authorId: ID!, postId: ID!): Comment!
    deleteComment(id: ID!): Boolean!
  }
`;

const resolvers = {
  Query: {
    users: async (_: any, args: { limit?: number; offset?: number }) => {
      return prisma.user.findMany({
        take: args.limit || 50,
        skip: args.offset || 0,
        orderBy: { createdAt: "desc" },
      });
    },

    user: async (_: any, args: { id: string }) => {
      return prisma.user.findUnique({ where: { id: args.id } });
    },

    posts: async (
      _: any,
      args: { published?: boolean; limit?: number; offset?: number }
    ) => {
      return prisma.post.findMany({
        where: args.published !== undefined ? { published: args.published } : {},
        take: args.limit || 50,
        skip: args.offset || 0,
        orderBy: { createdAt: "desc" },
      });
    },

    post: async (_: any, args: { id: string }) => {
      return prisma.post.findUnique({ where: { id: args.id } });
    },

    comments: async (_: any, args: { postId: string }) => {
      return prisma.comment.findMany({
        where: { postId: args.postId },
        orderBy: { createdAt: "asc" },
      });
    },
  },

  User: {
    posts: async (parent: any) => {
      return prisma.post.findMany({
        where: { authorId: parent.id },
        orderBy: { createdAt: "desc" },
      });
    },
    comments: async (parent: any) => {
      return prisma.comment.findMany({
        where: { authorId: parent.id },
        orderBy: { createdAt: "desc" },
      });
    },
  },

  Post: {
    author: async (parent: any) => {
      return prisma.user.findUnique({ where: { id: parent.authorId } });
    },
    comments: async (parent: any) => {
      return prisma.comment.findMany({
        where: { postId: parent.id },
        orderBy: { createdAt: "asc" },
      });
    },
  },

  Comment: {
    author: async (parent: any) => {
      return prisma.user.findUnique({ where: { id: parent.authorId } });
    },
    post: async (parent: any) => {
      return prisma.post.findUnique({ where: { id: parent.postId } });
    },
  },

  Mutation: {
    createUser: async (
      _: any,
      args: { name: string; email: string; bio?: string }
    ) => {
      return prisma.user.create({
        data: { name: args.name, email: args.email, bio: args.bio },
      });
    },

    updateUser: async (
      _: any,
      args: { id: string; name?: string; email?: string; bio?: string }
    ) => {
      return prisma.user.update({
        where: { id: args.id },
        data: {
          ...(args.name && { name: args.name }),
          ...(args.email && { email: args.email }),
          ...(args.bio !== undefined && { bio: args.bio }),
        },
      });
    },

    createPost: async (
      _: any,
      args: { title: string; content: string; authorId: string }
    ) => {
      return prisma.post.create({
        data: {
          title: args.title,
          content: args.content,
          authorId: args.authorId,
          published: false,
        },
      });
    },

    updatePost: async (
      _: any,
      args: { id: string; title?: string; content?: string; published?: boolean }
    ) => {
      return prisma.post.update({
        where: { id: args.id },
        data: {
          ...(args.title && { title: args.title }),
          ...(args.content && { content: args.content }),
          ...(args.published !== undefined && { published: args.published }),
        },
      });
    },

    deletePost: async (_: any, args: { id: string }) => {
      try {
        await prisma.comment.deleteMany({ where: { postId: args.id } });
        await prisma.post.delete({ where: { id: args.id } });
        return true;
      } catch (error: any) {
        throw new Error(`Failed to delete post: ${error.message}`);
      }
    },

    createComment: async (
      _: any,
      args: { body: string; authorId: string; postId: string }
    ) => {
      return prisma.comment.create({
        data: {
          body: args.body,
          authorId: args.authorId,
          postId: args.postId,
        },
      });
    },

    deleteComment: async (_: any, args: { id: string }) => {
      try {
        await prisma.comment.delete({ where: { id: args.id } });
        return true;
      } catch (error: any) {
        throw new Error(`Failed to delete comment: ${error.message}`);
      }
    },
  },
};

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: true,
});

async function main() {
  const { url } = await startStandaloneServer(server, {
    listen: { port: 4000 },
  });
  console.log(`GraphQL server ready at ${url}`);
}

main().catch(console.error);

export { resolvers, typeDefs };
