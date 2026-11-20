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
  const messages = [];

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

    if (messages.length >= 12) messages.splice(0, 2);
    messages.push({ role: "user", content });
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
        body: JSON.stringify({ messages }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "The personal assistant couldn't send your message.");

      messages.push({ role: "assistant", content: result.reply });
      appendMessage("assistant", result.reply);
    } catch (error) {
      appendMessage(
        "assistant",
        error instanceof Error ? error.message : "The personal assistant is temporarily unavailable.",
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
