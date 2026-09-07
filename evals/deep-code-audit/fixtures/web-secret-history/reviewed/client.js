export async function listProjects() {
    const response = await fetch("/api/projects");
    return response.json();
}
