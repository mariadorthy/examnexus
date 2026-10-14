import { beforeEach, describe, expect, it, vi } from "vitest";
import { deleteExamination } from "../services/examinationService";
import { jsonResponse, stubFetch } from "./helpers";

describe("examination deletion API", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("sends authenticated DELETE and returns the API response", async () => {
    localStorage.setItem("examnexus_token", "session-token");
    const fetchMock = stubFetch([
      ["DELETE /api/examinations/17", ({ init }) => {
        expect(init.headers.Authorization).toBe("Bearer session-token");
        return jsonResponse({ success: true, id: 17 });
      }],
    ]);

    await expect(deleteExamination(17)).resolves.toEqual({
      success: true,
      id: 17,
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("clears the session and dispatches unauthorized when DELETE returns 401", async () => {
    localStorage.setItem("examnexus_token", "expired-token");
    localStorage.setItem("examnexus_user", JSON.stringify({ role: "admin" }));
    const unauthorized = vi.fn();
    window.addEventListener("examnexus:unauthorized", unauthorized);
    stubFetch([
      ["DELETE /api/examinations/17", () =>
        jsonResponse({ message: "Authentication required." }, { status: 401 })],
    ]);

    await expect(deleteExamination(17)).rejects.toMatchObject({
      status: 401,
      message: "Authentication required.",
    });

    expect(localStorage.getItem("examnexus_token")).toBeNull();
    expect(localStorage.getItem("examnexus_user")).toBeNull();
    expect(unauthorized).toHaveBeenCalledTimes(1);
    window.removeEventListener("examnexus:unauthorized", unauthorized);
  });
});
