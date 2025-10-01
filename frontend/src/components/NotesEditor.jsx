import React, { useState } from "react";

export default function NotesEditor({ onSubmit }) {
  const [text, setText] = useState("");
  const [isPublic, setIsPublic] = useState(false);

  return (
    <div className="flex gap-2 items-center">
      <input
        className="border rounded px-2 py-1 w-64"
        placeholder={isPublic ? "Public reply…" : "Internal note…"}
        value={text}
        onChange={e => setText(e.target.value)}
      />
      <label className="text-xs flex items-center gap-1">
        <input type="checkbox" checked={isPublic} onChange={e => setIsPublic(e.target.checked)} />
        Public
      </label>
      <button
        className="border rounded px-2 py-1"
        onClick={() => { if (text.trim()) { onSubmit(text.trim(), isPublic); setText(""); } }}
      >
        Add
      </button>
    </div>
  );
}
