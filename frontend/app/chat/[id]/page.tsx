"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api, ApiError, type Chat } from "@/lib/api";
import { useRequireUser } from "@/lib/use-user";

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const user = useRequireUser();
  const [chat, setChat] = useState<Chat | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!user) return;
    api<Chat>(`/chats/${id}`)
      .then(setChat)
      .catch((e) => e instanceof ApiError && e.status === 404 && setNotFound(true));
  }, [user, id]);

  if (!user) return null;

  return (
    <main className="mx-auto max-w-2xl p-6">
      <Link href="/" className="text-sm underline">
        ← All chats
      </Link>
      {notFound ? (
        <p className="mt-6">Chat not found.</p>
      ) : chat ? (
        <>
          <h1 className="mt-4 text-xl font-semibold">{chat.title}</h1>
          <p className="mt-1 text-xs text-neutral-500">Thread id: {chat.id}</p>
          <p className="mt-6 rounded border bg-white p-4 text-sm text-neutral-600">
            Case picker and messaging arrive in later phases.
          </p>
        </>
      ) : null}
    </main>
  );
}
