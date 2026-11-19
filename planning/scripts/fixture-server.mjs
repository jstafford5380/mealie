import { createServer } from "node:http";

const recipe = {
  "@context": "https://schema.org",
  "@type": "Recipe",
  name: "Catalog Fixture Bread",
  description: "Synthetic local data for the Mealie UI catalog.",
  recipeYield: "6 servings",
  prepTime: "PT10M",
  cookTime: "PT30M",
  totalTime: "PT40M",
  recipeIngredient: ["2 cups flour", "1 cup water", "1 tsp salt"],
  recipeInstructions: [
    { "@type": "HowToStep", text: "Combine the ingredients in a bowl." },
    { "@type": "HowToStep", text: "Bake for 30 minutes." },
  ],
};

const server = createServer((request, response) => {
  const url = new URL(request.url ?? "/", "http://localhost");
  if (url.pathname.endsWith("/chat/completions")) {
    request.resume();
    setTimeout(() => {
      response.writeHead(503, { "Content-Type": "application/json" });
      response.end(JSON.stringify({ error: { message: "Synthetic catalog provider failure", type: "catalog_fixture", code: "catalog_fixture" } }));
    }, 5000);
    return;
  }
  if (url.pathname === "/recipe.html" || url.pathname === "/slow-recipe.html") {
    const data = { ...recipe, name: url.searchParams.get("name") || recipe.name };
    const send = () => {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(`<!doctype html><html><head><title>${data.name}</title><script type="application/ld+json">${JSON.stringify(data)}</script></head><body><h1>${data.name}</h1><p>${data.description}</p></body></html>`);
    };
    if (url.pathname === "/slow-recipe.html") setTimeout(send, 5000);
    else send();
    return;
  }
  response.writeHead(404);
  response.end("Catalog fixture not found");
});

server.listen(0, "0.0.0.0", () => {
  const address = server.address();
  console.log(`Catalog fixture server port: ${typeof address === "object" ? address.port : address}`);
});
for (const signal of ["SIGINT", "SIGTERM"]) process.on(signal, () => server.close(() => process.exit(0)));
