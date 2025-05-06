from __future__ import annotations
import requests 
from pydantic import Field    
import asyncio
import logging
from dotenv import load_dotenv
from typing import Any, Optional, Dict, List
import json
import httpx
import os
from typing import Any
from datetime import datetime
from livekit import rtc, api
from livekit.plugins.elevenlabs import tts
from livekit.plugins.deepgram import stt
from livekit.agents import (
    AgentSession,
    Agent,
    JobContext,
    function_tool,
    RunContext,
    get_job_context,
    cli,
    WorkerOptions,
    RoomInputOptions,
)
from livekit.plugins import (
    deepgram,
    openai,
    cartesia,
    silero,
   
)
from livekit.plugins import elevenlabs


# load environment variables, this is optional, only used for local development
load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("outbound-caller")
logger.setLevel(logging.INFO)

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")


class OutboundCaller(Agent):
    """
    AI outbound-calling agent responsible for:
      • looking up clinic knowledge-base entries
      • checking slot availability
      • updating / creating leads in the CRM
      • transferring or ending calls
    """

    def __init__(
        self,
        *,
        name: str,
        appointment_time: str,
        dial_info: Dict[str, Any],
    ) -> None:
        super().__init__(
            instructions = """
                {
                "form_data_of_user": {
                    "first_name": "Adam",
                    "email": "Booking@teraleads.com",
                    "last_name": "Taimash",
                    "lead_status": "Appointment",
                    "lead_type": "AI_call_lead",
                    "note_for_doctor": null,
                    "phone_number": "+16474944500",
                    "phone_verify": "unverified",
                    "treatment": "perment teeth implant full arch ",
                    "utm_medium": null,
                    "utm_source": null,
                    "unique_id": null,
                    "website_user_name": "indianaimplantclinic",
                    "website_name": "indiana implant clinic",
                    "annual_salary": "4500",
                    "appointment_status": "Not Confirmed",
                    "how_to_contact": null,
                    "treatment_value": 26990,
                    "appointment_date_time": "2025-05-05 08:00:00",
                    "appointment_date_time_end": "2025-05-05 08:30:00",
                    "appointment_duration": "30",
                    "appointment_time": null,
                    "created_on": "2025-04-30T12:57:18.164Z",
                    "updated_on": "2025-04-30T12:57:18.164Z",
                    "User": null
                }
                You will start the conversation with user data from{{form_data_of_user}} first with the user {{first_name}} {{last_name}}.
                
                system message: current date 2025-05-05
                }
                workflow:
                Script Configuration:
                {
                "script_name": "AI Appointment Specialist Script (Outbound Calls)",
                "clinic_name": "indiana implant clinic",
                "agent_name": "Anna",
                "guardrail": "Anna must keep all responses within the context of dental care or clinic-related operations. She may answer questions about office hours, location, payment methods, dentist names, and financing. If a lead brings up something unrelated, politely say: “I’m here to assist with dental or appointment-related questions for indianaimplantclinic.”",
                "tone": {
                    "style": "friendly and assertive",
                    "avoid": "vague or passive language"
                },
                "initial_dialogue": [
                    {
                    "speaker": "Anna",
                    "text": "Hey, this is Anna from Indiana Implant Clinic. I’m calling back to follow up on the form you submitted requesting a free consultation. Do you have a moment?"
                    },
                    {
                    "condition": "if YES",
                    "text": "Wonderful! Am I speaking with {{first_name}}{{last_name}}?"
                    },
                    {
                    "condition": "if name is unclear",
                    "text": "No worries—could you please spell out your full name so I can confirm it correctly?"
                    },
                    {
                    "speaker": "Anna",
                    "text": "Great to meet you, Adam! Let’s find a time that works for your consultation. What day and time would you prefer?"
                    },
                    {
                    "action": "api",
                    "call": "look_up_availability",
                    "params": {
                        "appointment_date": "{{appointment_date}}",
                        "appointment_time": "{{appointment_time}}"
                    },
                    "system": "If that time is available, proceed. If not, offer next available options."
                    }
                ],
                "contact_info_collection": [
                    {
                    "speaker": "Anna",
                    "text": "What’s the best phone number to confirm the appointment?"
                    },
                    {
                    "action": "store {{phone_number}}"
                    },
                    {
                    "speaker": "Anna",
                    "text": "Thanks! And your email address for confirmation?"
                    },
                    {
                    "action": "store {{email}}"
                    }
                ],
                "final_confirmation": [
                    
                {
                "call_function": "update_lead",
                "params": {
                "id": 2936249,
                "clinic_id": 34,
                "assigned_id": 5,
                "assign_to": "Anna",  
                "email": "{{email}}",
                "email_verify": "verified",
                "finance_score": "High",
                "credit_score": "111",
                "first_name": "{{first_name}}",
                "form_status": "Completed",
                "gcld_google": "Updated GCLD Data",
                "ip_address": "192.168.1.1",
                "last_name": "{{last_name}}",
                "lead_status": "Closed",
                "lead_type": "New Type",
                "note_for_doctor": "Updated note for the doctor.",
                "phone_number": "{{phone_number}}",
                "phone_verify": "verified",
                "treatment": "{{treatment}}",
                "utm_campaign": "Updated Campaign",
                "utm_medium": "Updated Medium",
                "utm_source": "Updated Source",
                "unique_id": "unique12345",
                "website_user_name": "UpdatedUser",
                "website_name": "indiana implant clinic",
                "home_owner": "Yes",
                "co_signer": "No",
                "annual_salary": "60000",
                "appointment_status": "Confirmed",
                "how_to_contact": "",
                "treatment_value": 5000,
                "appointment_date_time": {{"2025-01-21 10:30:00"}},
                "appointment_date_time_end": {{"2025-01-21 11:00:00"}},
                "appointment_duration": "30",
                "appointment_time": "",
                "appointment_notes": "Updated appointment notes.",
                "contacted_attempts": "3",
                "close_amount": 4500,
                "recording_url": "http://recording-url.com",
                "phone_number_to": "+9876543210",
                "call_session_id": "session12345",
                "hangup_cause": "No Answer",
                "call_start_time": "2025-01-21 10:00:00",
                "conversations_lead": true,
                "ai_call": false,
                "avatar_color": "#FF5733"
                }
            },
            {
                    "speaker": "Anna",
                    "text": "Perfect! You’re booked for a consultation on {{appointment_date}} at {{appointment_time}} with Dr. Ricky Singh. We’ll send confirmation to {{phone_number}} and {{email}} shortly."
                    },
            {
                "speaker": "Anna",
                "text": "Looking forward to seeing you then, {{first_name}}! Take care!"
            }
            ]
                }
                """
              
        )
        self.participant: Optional[rtc.RemoteParticipant] = None
        self.dial_info = dial_info

    def set_participant(self, participant: rtc.RemoteParticipant) -> None:
        self.participant = participant

    async def hangup(self) -> None:
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=job_ctx.room.name)
        )

    @function_tool(description="Fetch the clinic knowledge base by clinic ID:34 and use it if user asks about clinic ofical timings of clinic, treatments types and there prices,if user needs any information abut indiana implant clinic ")
    async def get_clinic_knowledge_base(self, ctx: RunContext, clinic_id: str = "34") -> Dict[str, Any]:
        url = "https://dev.teracrm.ai/api/v1/auth/getClinicKnowledgeBaseDetails"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ik51bWFueW91c2FmemFpMTIzQGdtYWlsLmNvbSIsImlhdCI6MTc0MDEzMjMzMX0.ki6bs6LcovamtZrUpeLWZ3QFbwL-oKhvDvCTEmHaDZM",
        }
        payload = {"clinic_id": "34"}

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                self.clinic_knowledge_base = data
                return {"status": "success", "data": data}
        except httpx.HTTPStatusError as e:
            logging.error("HTTP error: %s", e)
            return {"status": "error", "message": f"HTTP error: {e.response.status_code}"}
        except httpx.RequestError as e:
            logging.error("Request failed: %s", e)
            return {"status": "error", "message": str(e)}

    @function_tool()
    async def transfer_call(self, ctx: RunContext) -> str:
        transfer_to: str | None = self.dial_info.get("transfer_to")
        if not transfer_to:
            return "No transfer number configured."

        logging.info("Transferring call to %s", transfer_to)
        await ctx.session.generate_reply(instructions="Sure, one moment while I transfer you.")
        job_ctx = get_job_context()
        try:
            await job_ctx.api.sip.transfer_sip_participant(
                api.TransferSIPParticipantRequest(
                    room_name=job_ctx.room.name,
                    participant_identity=self.participant.identity,
                    transfer_to=f"tel:{transfer_to}",
                )
            )
            return f"Transferred to {transfer_to}."
        except Exception as e:
            logging.error("Transfer failed: %s", e)
            await ctx.session.generate_reply(instructions="Apologies, something went wrong transferring the call.")
            await self.hangup()
            return "Transfer failed."

    @function_tool()
    async def end_call(self, ctx: RunContext) -> str:
        logging.info("Ending call for %s", self.participant.identity if self.participant else "unknown")
        current = ctx.session.current_speech
        if current:
            await current.wait_for_playout()
        await self.hangup()
        return "Call ended."

    @function_tool(
    description="Check slot availability. Dates 'YYYY-MM-DD', times 'HH:MM' or 'HH:MMAM/PM'. condition: current date is  friday 2025-05-02 so if user tell day" \
    "like monday tusday so calculate the date and pass as parameter. another condition satueday and sunday are closed so dont take just tell we are off on satueday and friday")
    async def look_up_availability(self, ctx: RunContext, website_name: str, appointment_date: str, appointment_time: str) -> Dict[str, Any]:
        try:
            datetime.strptime(appointment_date, "%Y-%m-%d")
        except ValueError:
            return {"available": False, "message": "Invalid date. Format should be YYYY-MM-DD."}

        try:
            time_obj = datetime.strptime(appointment_time, "%I:%M%p")
            appointment_time_24h = time_obj.strftime("%H:%M")
        except ValueError:
            try:
                datetime.strptime(appointment_time, "%H:%M")
                appointment_time_24h = appointment_time
            except ValueError:
                return {"available": False, "message": "Invalid time. Say it like '02:30PM' or '14:30'."}

        api_url = "https://dev.teracrm.ai/api/v1/auth/checkClinicSlotAvailability"
        dup_time = f"{appointment_time_24h} {appointment_time_24h}"
        payload = {
            "website_name": "indianaimplantclinic",
            "appointment_date": appointment_date,
            "appointment_time": dup_time,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ik51bWFueW91c2FmemFpMTIzQGdtYWlsLmNvbSIsImlhdCI6MTc0MDEzMjMzMX0.ki6bs6LcovamtZrUpeLWZ3QFbwL-oKhvDvCTEmHaDZM",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(api_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

                if not data.get("success", False):
                    message = data.get("message", "Unknown error from slot availability API.")
                    logging.warning("Slot availability API returned error: %s", message)
                    return {"available": False, "message": message}

                if data.get("slotAvailable"):
                    return {"available": True, "message": f"{appointment_date} {appointment_time} is free."}

                alt = data.get("slots", {}).get("available", [])
                return {"available": False, "alternatives": alt[:3]}
        except httpx.RequestError as e:
            logging.error("Availability lookup failed: %s", e)
            return {"available": False, "message": str(e)}

    @function_tool(description="when you confirm all details please call this api to upgrade details and send text and email conformation to user.all parameters are set just update first_name last_name email phone_number treatment",
    )          
    async def update_lead(
        self,
        ctx: RunContext,
        *,
        id: int = 2936249,
        clinic_id: int = 34,
        assigned_id: int = 5,
        assign_to: str ,
        email: str,
        email_verify: str = "verified",
        finance_score: str = "High",
        credit_score: str = "750",
        first_name: str ,
        form_status: str = "Completed",
        gcld_google: str = "Updated GCLD Data",
        ip_address: str = "192.168.1.1",
        last_name: str ,
        lead_status: str = "Closed",
        lead_type: str = "New Type",
        note_for_doctor: str = "Updated note for the doctor.",
        phone_number: str ,
        phone_verify: str = "verified",
        treatment: str ,
        utm_campaign: str = "Updated Campaign",
        utm_medium: str = "Updated Medium",
        utm_source: str = "Updated Source",
        unique_id: str = "unique12345",
        website_user_name: str = "UpdatedUser",
        website_name: str = "indiana implant clinic",
        home_owner: str = "Yes",
        co_signer: str = "No",
        annual_salary: str = "60000",
        appointment_status: str = "Confirmed",
        how_to_contact: str = "",
        treatment_value: int = 5000,
        appointment_date_time: str = "2025-01-21 10:30:00",
        appointment_date_time_end: str = "2025-01-21 11:00:00",
        appointment_duration: str = "30",
        appointment_time: str = "",
        appointment_notes: str = "Updated appointment notes.",
        contacted_attempts: str = "3",
        close_amount: int = 4500,
        recording_url: str = "http://recording-url.com",
        phone_number_to: str = "+9876543210",
        call_session_id: str = "session12345",
        hangup_cause: str = "No Answer",
        call_start_time: str = "2025-01-21 10:00:00",
        conversations_lead: bool = True,
        ai_call: bool = False,
        avatar_color: str = "#FF5733"
    ) -> Dict[str, Any]:
        api_url = "http://161.35.55.97:5000/api/v1/auth/update-leads"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ik51bWFueW91c2FmemFpMTIzQGdtYWlsLmNvbSIsImlhdCI6MTc0MDEzMjMzMX0.ki6bs6LcovamtZrUpeLWZ3QFbwL-oKhvDvCTEmHaDZM",
        }
        payload: Dict[str, Any] = {
            'id': id,
            'clinic_id': clinic_id,
            "assigned_id": assigned_id,
            "assign_to": assign_to,
            "email": email,
            "email_verify": email_verify,
            "finance_score": finance_score,
            "credit_score": credit_score,
            "first_name": first_name,
            "form_status": form_status,
            "gcld_google": gcld_google,
            "ip_address": ip_address,
            "last_name": last_name,
            "lead_status": lead_status,
            "lead_type": lead_type,
            "note_for_doctor": note_for_doctor,
            "phone_number": phone_number,
            "phone_verify": phone_verify,
            "treatment": treatment,
            "utm_campaign": utm_campaign,
            "utm_medium": utm_medium,
            "utm_source": utm_source,
            "unique_id": unique_id,
            "website_user_name": website_user_name,
            "website_name": website_name,
            "home_owner": home_owner,
            "co_signer": co_signer,
            "annual_salary": annual_salary,
            "appointment_status": appointment_status,
            "how_to_contact": how_to_contact,
            "treatment_value": treatment_value,
            "appointment_date_time": appointment_date_time,
            "appointment_date_time_end": appointment_date_time_end,
            "appointment_duration": appointment_duration,
            "appointment_time": appointment_time,
            "appointment_notes": appointment_notes,
            "contacted_attempts": contacted_attempts,
            "close_amount": close_amount,
            "recording_url": recording_url,
            "phone_number_to": phone_number_to,
            "call_session_id": call_session_id,
            "hangup_cause": hangup_cause,
            "call_start_time": call_start_time,
            "conversations_lead": conversations_lead,
            "ai_call": ai_call,
            "avatar_color": avatar_color
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(api_url, headers=headers, json=payload)
                resp.raise_for_status()
                logging.info("Lead update response: %s", resp.json())
                return resp.json()
        except httpx.RequestError as e:
            logging.error("Lead update failed: %s", e)
            return {"status": "error", "message": str(e)}
    @function_tool(description="Fetch leads filtered by email and website name.")
    async def get_leads(self, ctx: RunContext, *, email: str, website_name: str = "indianaimplantclinic", page: int = 1, limit: int = 10, search_type: str = "text") -> Dict[str, Any]:
        url = "http://161.35.55.97:5000/api/v1/auth/get-leads"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Ik51bWFueW91c2FmemFpMTIzQGdtYWlsLmNvbSIsImlhdCI6MTc0MDEzMjMzMX0.ki6bs6LcovamtZrUpeLWZ3QFbwL-oKhvDvCTEmHaDZM",
        }
        payload = {
            "page": page,
            "limit": limit,
            "search": email,
            "websiteNames": [website_name],
            "searchType": search_type,
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                return {"status": "success", "data": resp.json()}
        except httpx.RequestError as e:
            logging.error("get_leads error: %s", e)
            return {"status": "error", "message": str(e)}

    @function_tool()
    async def detected_answering_machine(self, ctx: RunContext) -> str:
        logging.info("Voicemail detected; hanging up.")
        await self.hangup()
        return "Voicemail – call ended."


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect()
    metadata = ctx.job.metadata
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:
            metadata = {"phone_number": metadata}
    phone_number = metadata.get("phone_number")
    participant_identity = phone_number
    # look up the user's phone number and appointment details
    agent = OutboundCaller(
        name="Jayden",
        appointment_time="next Tuesday at 3pm",
        dial_info=participant_identity,
    )
    eleven_tts = tts.TTS(
    api_key="sk_b179d6c09757ec2cb015f23121ac91778193c75006938954",
    model="eleven_turbo_v2_5",
    voice_id="5MRtDX7fpi72xPHrBDUS",  # Direct parameter
    voice_settings=tts.VoiceSettings(
        stability=0.71,
        similarity_boost=0.7,
        style=0.2,
        use_speaker_boost=True
    ),
    language="en",
    enable_ssml_parsing=False,
    chunk_length_schedule=[80, 120, 200, 260]
)
    deepgram_stt = stt.STT(
        model="nova-2-general",
        interim_results=True,
        smart_format=True,
        punctuate=True,
        filler_words=True,
        profanity_filter=False,
        keywords=[("LiveKit", 1.5)],
        language="en-US",
    )

    latest_image: rtc.VideoFrame | None = None
    human_agent_present = False
    # the following uses GPT-4o, Deepgram and Cartesia
    session = AgentSession(
        
        vad=silero.VAD.load(),
        stt=deepgram_stt,
        # you can also use OpenAI's TTS with openai.TTS()
        tts=eleven_tts,
        llm=openai.LLM(model="gpt-4o"),
        # you can also use a speech-to-speech model like OpenAI's Realtime API
        # llm=openai.realtime.RealtimeModel()
    )

    # start the session first before dialing, to ensure that when the user picks up
    # the agent does not miss anything the user says
    session_started = asyncio.create_task(
        session.start(
            agent=agent,
            room=ctx.room,
            room_input_options=RoomInputOptions(
                # enable Krisp background voice and noise removal
                # noise_cancellation=noise_cancellation.BVC(),
            ),
        )
    )

    # `create_sip_participant` starts dialing the user
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=participant_identity,
                # function blocks until user answers the call, or if the call fails
                wait_until_answered=True,
            )
        )

        # wait for the agent session start and participant join
        await session_started
        participant = await ctx.wait_for_participant(identity=participant_identity)
        logger.info(f"participant joined: {participant.identity}")

        agent.set_participant(participant)

    except api.TwirpError as e:
        logger.error(
            f"error creating SIP participant: {e.message}, "
            f"SIP status: {e.metadata.get('sip_status_code')} "
            f"{e.metadata.get('sip_status')}"
        )
        ctx.shutdown()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="outbound-caller",
        )
    )
