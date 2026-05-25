import fs from "fs/promises";
import path from "path";
import { randomUUID } from "crypto";

const dataDir = path.resolve("data");
const dataFile = path.join(dataDir, "users.json");

const ensureDataFile = async () => {
    try {
        await fs.mkdir(dataDir, { recursive: true });
        await fs.access(dataFile);
    } catch {
        await fs.writeFile(dataFile, "[]", "utf-8");
    }
};

const readUsers = async () => {
    await ensureDataFile();
    const raw = await fs.readFile(dataFile, "utf-8");
    return raw ? JSON.parse(raw) : [];
};

const writeUsers = async (users) => {
    await ensureDataFile();
    await fs.writeFile(dataFile, JSON.stringify(users, null, 2), "utf-8");
};

export const findUserByEmail = async (email) => {
    const normalizedEmail = email.trim().toLowerCase();
    const users = await readUsers();
    return users.find((user) => user.email === normalizedEmail);
};

export const findUserById = async (id) => {
    const users = await readUsers();
    return users.find((user) => user.id === id);
};

export const findUserByRefreshToken = async (refreshToken) => {
    const users = await readUsers();
    return users.find((user) => user.refreshToken === refreshToken);
};

export const createUser = async ({ email, name, passwordHash }) => {
    const normalizedEmail = email.trim().toLowerCase();
    const users = await readUsers();

    if (users.some((user) => user.email === normalizedEmail)) {
        throw new Error("User already exists");
    }

    const role = users.length === 0 ? "admin" : "user";
    const newUser = {
        id: randomUUID(),
        email: normalizedEmail,
        name: name?.trim() || normalizedEmail.split("@")[0],
        role,
        passwordHash,
        createdAt: new Date().toISOString(),
    };

    users.push(newUser);
    await writeUsers(users);
    return newUser;
};

export const updateUser = async (id, updates) => {
    const users = await readUsers();
    const index = users.findIndex((user) => user.id === id);
    if (index === -1) {
        return null;
    }
    users[index] = { ...users[index], ...updates };
    await writeUsers(users);
    return users[index];
};

export { readUsers };
