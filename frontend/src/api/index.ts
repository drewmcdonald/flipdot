import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";
import type { paths } from "./schema"; // generated by openapi-typescript

const api = createClient(
  createFetchClient<paths>({
    baseUrl: "http://localhost:8000",
  })
);

export default api;
