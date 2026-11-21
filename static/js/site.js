const menuToggle = document.querySelector(".menu-toggle");
const navigation = document.querySelector(".navigation");

if (menuToggle && navigation) {
  menuToggle.addEventListener("click", () => {
    const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", String(!isOpen));
    navigation.classList.toggle("is-open", !isOpen);
  });

  navigation.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuToggle.setAttribute("aria-expanded", "false");
      navigation.classList.remove("is-open");
    });
  });
}

const smalltalk = document.querySelector(".smalltalk");

if (smalltalk) {
  const launcher = smalltalk.querySelector(".smalltalk-launcher");
  const panel = smalltalk.querySelector(".smalltalk-panel");
  const closeButton = smalltalk.querySelector(".smalltalk-close");
  const form = smalltalk.querySelector(".smalltalk-form");
  const input = smalltalk.querySelector("#smalltalk-input");
  const transcript = smalltalk.querySelector(".smalltalk-messages");
  const sendButton = form.querySelector('button[type="submit"]');
  const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;

  const setOpen = (isOpen) => {
    panel.hidden = !isOpen;
    panel.setAttribute("aria-hidden", String(!isOpen));
    launcher.setAttribute("aria-expanded", String(isOpen));
    if (isOpen) input.focus();
    else launcher.focus();
  };

  const appendMessage = (role, content, isError = false) => {
    const message = document.createElement("p");
    message.className = `smalltalk-message smalltalk-message-${role}`;
    if (isError) message.classList.add("smalltalk-message-error");
    message.textContent = content;
    transcript.append(message);
    transcript.scrollTop = transcript.scrollHeight;
    return message;
  };

  launcher.addEventListener("click", () => setOpen(true));
  closeButton.addEventListener("click", () => setOpen(false));
  panel.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setOpen(false);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const content = input.value.trim();
    if (!content || sendButton.disabled) return;

    appendMessage("user", content);
    input.value = "";
    sendButton.disabled = true;
    form.setAttribute("aria-busy", "true");
    const thinking = document.createElement("p");
    thinking.className = "smalltalk-message smalltalk-message-assistant";
    thinking.textContent = "Thinking...";
    transcript.append(thinking);
    transcript.scrollTop = transcript.scrollHeight;

    try {
      const response = await fetch(smalltalk.dataset.chatUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ messages: [{ role: "user", content }] }),
      });
      const contentType = response.headers.get("Content-Type") || "";
      if (!response.ok) {
        const result = await response.json();
        throw new Error(result.error || "The AI assistant couldn't send your message.");
      }
      if (!contentType.includes("text/event-stream") || !response.body) {
        throw new Error("The AI assistant returned an invalid response.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let reply = "";
      let assistantMessage = null;

      const processEventBlock = (eventBlock) => {
        let eventName = "message";
        let eventData = "";
        for (const line of eventBlock.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n")) {
          if (line.startsWith("event:")) eventName = line.slice(6).trim();
          if (line.startsWith("data:")) {
            eventData += `${eventData ? "\n" : ""}${line.slice(5).trimStart()}`;
          }
        }
        if (!eventData) return;

        if (!/^[0-9a-f]+$/i.test(eventData)) {
          throw new Error("The AI assistant returned an invalid streaming response.");
        }
        const bytes = new Uint8Array(eventData.match(/.{2}/g).map((pair) => parseInt(pair, 16)));
        const text = new TextDecoder().decode(bytes);

        if (eventName === "error") {
          throw new Error(text || "The AI assistant couldn't generate a reply.");
        }
        if (eventName === "done") return;

        reply += text;
        if (!assistantMessage) {
          thinking.remove();
          assistantMessage = appendMessage("assistant", reply);
        } else {
          assistantMessage.textContent = reply;
          transcript.scrollTop = transcript.scrollHeight;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          buffer += decoder.decode();
          break;
        }
        buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n").replace(/\r/g, "\n");

        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const eventBlock = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          processEventBlock(eventBlock);
          boundary = buffer.indexOf("\n\n");
        }
      }
      if (buffer.trim()) processEventBlock(buffer);

      if (!reply) throw new Error("The AI assistant couldn't generate a reply.");
    } catch (error) {
      appendMessage(
        "assistant",
        error instanceof Error ? error.message : "The AI assistant is temporarily unavailable.",
        true,
      );
    } finally {
      thinking.remove();
      sendButton.disabled = false;
      form.removeAttribute("aria-busy");
      input.focus();
    }
  });
}
