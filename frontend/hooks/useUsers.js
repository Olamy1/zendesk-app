// hooks/useUsers.js
import { useEffect, useState } from "react";
import { getUsers } from "../services/backendAPI";

export default function useUsers(authToken) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const data = await getUsers(authToken);
        setUsers(data.users || []);
      } catch (e) {
        console.error("User fetch failed:", e);
        setErr("Failed to fetch users.");
      } finally {
        setLoading(false);
      }
    })();
  }, [authToken]);

  return { users, loading, err };
}
