// AI-generated PR — review this code
// Description: Added WebSocket server for real-time chat with rooms
// Implements a multi-room chat server using the ws library. Clients can
// join rooms, send messages, and see who is in each room.

import { WebSocketServer, WebSocket } from "ws";
import { IncomingMessage } from "http";
import { v4 as uuidv4 } from "uuid";

interface Client {
  id: string;
  ws: WebSocket;
  username: string;
  room: string;
}

interface ChatMessage {
  type: "join" | "leave" | "message" | "members" | "error";
  room?: string;
  username?: string;
  content?: string;
  members?: string[];
  timestamp?: number;
}

const rooms: Map<string, Set<Client>> = new Map();
const clients: Map<string, Client> = new Map();

function broadcast(room: string, message: ChatMessage, exclude?: string) {
  const roomClients = rooms.get(room);
  if (!roomClients) return;

  const payload = JSON.stringify(message);
  for (const client of roomClients) {
    if (client.id !== exclude && client.ws.readyState === WebSocket.OPEN) {
      client.ws.send(payload);
    }
  }
}

function getRoomMembers(room: string): string[] {
  const roomClients = rooms.get(room);
  if (!roomClients) return [];
  return Array.from(roomClients).map((c) => c.username);
}

function joinRoom(client: Client, room: string) {
  // Leave current room if any
  if (client.room) {
    leaveRoom(client);
  }

  client.room = room;

  if (!rooms.has(room)) {
    rooms.set(room, new Set());
  }
  rooms.get(room)!.add(client);

  // Notify room of new member
  broadcast(
    room,
    {
      type: "join",
      room,
      username: client.username,
      content: `${client.username} joined the room`,
      timestamp: Date.now(),
    },
    client.id
  );

  // Send member list to the joining client
  client.ws.send(
    JSON.stringify({
      type: "members",
      room,
      members: getRoomMembers(room),
    })
  );
}

function leaveRoom(client: Client) {
  const room = client.room;
  if (!room) return;

  const roomClients = rooms.get(room);
  if (roomClients) {
    roomClients.delete(client);
    if (roomClients.size === 0) {
      rooms.delete(room);
    }
  }

  broadcast(room, {
    type: "leave",
    room,
    username: client.username,
    content: `${client.username} left the room`,
    timestamp: Date.now(),
  });

  client.room = "";
}

export function createChatServer(port: number) {
  const wss = new WebSocketServer({ port });

  console.log(`WebSocket chat server running on port ${port}`);

  wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
    const clientId = uuidv4();
    const client: Client = {
      id: clientId,
      ws,
      username: `user_${clientId.slice(0, 8)}`,
      room: "",
    };

    clients.set(clientId, client);
    console.log(`Client connected: ${clientId}`);

    ws.on("message", (data: Buffer) => {
      let parsed: any;
      try {
        parsed = JSON.parse(data.toString());
      } catch {
        ws.send(JSON.stringify({ type: "error", content: "Invalid JSON" }));
        return;
      }

      switch (parsed.type) {
        case "set_username":
          client.username = parsed.username || client.username;
          break;

        case "join":
          const roomName = parsed.room;
          if (!roomName || typeof roomName !== "string") {
            ws.send(
              JSON.stringify({ type: "error", content: "Room name required" })
            );
            return;
          }
          joinRoom(client, roomName);
          break;

        case "message":
          if (!client.room) {
            ws.send(
              JSON.stringify({
                type: "error",
                content: "Join a room first",
              })
            );
            return;
          }

          const chatMsg: ChatMessage = {
            type: "message",
            room: client.room,
            username: client.username,
            content: parsed.content,
            timestamp: Date.now(),
          };

          // Broadcast to everyone in the room including sender
          broadcast(client.room, chatMsg);
          break;

        case "leave":
          leaveRoom(client);
          break;

        default:
          ws.send(
            JSON.stringify({ type: "error", content: "Unknown message type" })
          );
      }
    });

    ws.on("close", () => {
      console.log(`Client disconnected: ${clientId}`);
      if (client.room) {
        leaveRoom(client);
      }
      // Note: client cleanup is handled by room leave
    });

    ws.on("error", (err: Error) => {
      console.error(`WebSocket error for ${clientId}:`, err.message);
    });
  });

  return wss;
}

// Start server if run directly
const PORT = parseInt(process.env.WS_PORT || "8080", 10);
createChatServer(PORT);
