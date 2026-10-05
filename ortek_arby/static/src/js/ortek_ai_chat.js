/** @odoo-module **/

import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class AiCompanyDashboard extends Component {
    static template = "ortek_arby.AiCompanyDashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.chatContainerRef = useRef("chatContainer");

        this.state = useState({
            messages: [
                {
                    id: 1,
                    sender: "ai",
                    text: "Olá! Sou o assistente ORTEK AI. Como posso ajudar na gestão dos seus pedidos ou processos fiscais hoje?",
                    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                },
            ],
            inputMessage: "",
            isLoading: false,
        });
    }

    async sendMessage() {
        const text = this.state.inputMessage.trim();
        if (!text || this.state.isLoading) {
            return;
        }

        const userMsg = {
            id: Date.now(),
            sender: "user",
            text: text,
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        this.state.messages.push(userMsg);
        this.state.inputMessage = "";
        this.state.isLoading = true;
        this.scrollToBottom();

        try {
            const response = await this.orm.call(
                "ortek.ai.engine",
                "get_ai_response",
                [text],
                {}
            );

            const aiMsg = {
                id: Date.now() + 1,
                sender: "ai",
                text: response || "Não foi possível obter uma resposta do motor de IA.",
                time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            };

            this.state.messages.push(aiMsg);
        } catch (error) {
            this.notification.add("Erro ao comunicar com a ORTEK AI: " + error.message, {
                type: "danger",
            });
        } finally {
            this.state.isLoading = false;
            this.scrollToBottom();
        }
    }

    onKeydown(ev) {
        if (ev.key === "Enter" && !ev.shiftKey) {
            ev.preventDefault();
            this.sendMessage();
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.chatContainerRef.el) {
                this.chatContainerRef.el.scrollTop = this.chatContainerRef.el.scrollHeight;
            }
        }, 100);
    }
}

registry.category("actions").add("ai_company_dashboard_tag", AiCompanyDashboard);