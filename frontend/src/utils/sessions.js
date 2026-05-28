const sessionKey = (uid) => `sessions_${uid}`;
const activeKey = (uid) => `activeSessionId_${uid}`;

export const getSessions = (userId) => {
    try {
        const raw = localStorage.getItem(sessionKey(userId));
        return raw ? JSON.parse(raw) : [];
    } catch { return []; }
};

const persist = (userId, sessions) => {
    localStorage.setItem(sessionKey(userId), JSON.stringify(sessions));
};

export const getActiveSessionId = (userId) => {
    return localStorage.getItem(activeKey(userId));
};

export const setActiveSessionId = (userId, id) => {
    localStorage.setItem(activeKey(userId), id);
};

export const createSession = (userId) => {
    const sessions = getSessions(userId);
    const session = {
        id: crypto.randomUUID(),
        title: "New chat",
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
    };
    sessions.push(session);
    persist(userId, sessions);
    setActiveSessionId(userId, session.id);
    return session;
};

export const updateSession = (userId, sessionId, updates) => {
    const sessions = getSessions(userId);
    const idx = sessions.findIndex(s => s.id === sessionId);
    if (idx === -1) return null;
    sessions[idx] = { ...sessions[idx], ...updates, updatedAt: new Date().toISOString() };
    persist(userId, sessions);
    return sessions[idx];
};

export const deleteSession = (userId, sessionId) => {
    const sessions = getSessions(userId).filter(s => s.id !== sessionId);
    persist(userId, sessions);
    return sessions;
};

export const generateTitle = (messages) => {
    const first = messages.find(m => m.role === "user");
    if (!first) return "New chat";
    const text = typeof first.content === "string" ? first.content : "";
    return text.length > 50 ? text.slice(0, 50) + "..." : text;
};
