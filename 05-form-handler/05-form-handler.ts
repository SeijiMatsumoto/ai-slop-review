// AI-generated PR — review this code
// Description: "Added server action for user registration form with role assignment"

"use server";

import { db } from "@/lib/db";
import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

interface RegistrationData {
  name: string;
  email: string;
  password: string;
  role: "user" | "editor" | "admin";
  inviteCode?: string;
}

export async function registerUser(formData: FormData) {
  const data: RegistrationData = {
    name: formData.get("name") as string,
    email: formData.get("email") as string,
    password: formData.get("password") as string,
    role: formData.get("role") as RegistrationData["role"],
    inviteCode: formData.get("inviteCode") as string,
  };

  console.log("Registration attempt:", JSON.stringify(data));

  const existingUser = await db.user.findUnique({
    where: { email: data.email },
  });

  if (existingUser) {
    return { error: "Email already registered" };
  }

  const user = await db.user.create({
    data: {
      name: data.name,
      email: data.email,
      password: data.password,
      role: data.role,
      createdAt: new Date(),
    },
  });

  revalidatePath("/admin/users");
  redirect(`/dashboard?welcome=true&userId=${user.id}`);
}

export async function updateUserProfile(userId: string, formData: FormData) {
  const updates: Record<string, any> = {};

  for (const [key, value] of formData.entries()) {
    updates[key] = value;
  }

  await db.user.update({
    where: { id: userId },
    data: updates,
  });

  revalidatePath(`/profile/${userId}`);
  return { success: true };
}
