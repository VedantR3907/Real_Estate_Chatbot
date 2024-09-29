import asyncio
import streamlit as st
from streamlit_extras.bottom_container import bottom
from utils.query_database import llamaindex_chatbot
from utils.chat_history.chat_history import display_chat_history, read_chat_history, format_chat_history_llamaindex
from utils.chat_history.save_data_to_json import save_to_json
from utils.user_data.generate_json import save_user_metadata
from utils.query_without_database import chat_with_llm
from utils.query_agents import crewai_agent_chat

def input_user_information():
    """Display input fields for user information using an expander."""
    # Initialize expander visibility state
    if "expander_visible" not in st.session_state:
        st.session_state.expander_visible = True

    # Only show expander if expander_visible is True
    if st.session_state.expander_visible:
        expander = st.expander("User Information", expanded=False)
        with expander:
            user_type = st.selectbox("Select your role:", ("Buyer", "Seller", "Tenant", "Landlord"))
            if 'user_type' not in st.session_state:
                st.session_state['user_type'] = ''
            # Generate unique key based on the user type
            if user_type == "Buyer":
                name = st.text_input("Name", key="buyer_name")
                property_type = st.text_input("Property Type", key="buyer_property_type")
                budget = st.number_input("Budget in dollar", key="buyer_budget")
                preferred_location = st.text_input("Preferred Location", key="buyer_preferred_location")
                if st.button("Submit", key="buyer_submit"):
                    st.session_state['user_type'] = 'buyer'
                    user_info = {
                        "name": name,
                        "property_type": property_type,
                        "budget_in_dollar": budget,
                        "preferred_location": preferred_location
                    }
                    save_user_metadata("buyer", user_info)  # Save the user info
                    st.session_state.expander_visible = False  # Hide the expander
                    return {
                        "user_type": user_type,
                        "information": user_info
                    }
            
            elif user_type == "Seller":
                name = st.text_input("Name", key="seller_name")
                property_type = st.text_input("Property Type", key="seller_property_type")
                location = st.text_input("Location", key="seller_location")
                selling_price = st.text_input("Selling Price", key="seller_selling_price")
                property_specific = st.text_input("Property specifics (floor, sq.ft etc.)", key='landlord_property_specific')
                if st.button("Submit", key="seller_submit"):
                    st.session_state['user_type'] = 'seller'
                    user_info = {
                        "name": name,
                        "property_type": property_type,
                        "location": location,
                        "selling_price": selling_price,
                        "property_specifics": property_specific
                    }
                    save_user_metadata("seller", user_info)  # Save the user info
                    st.session_state.expander_visible = False  # Hide the expander
                    return {
                        "user_type": user_type,
                        "information": user_info
                    }

            elif user_type == "Tenant":
                name = st.text_input("Name", key="tenant_name")
                property_type = st.text_input("Property Type", key="tenant_property_type")
                budget = st.number_input("Budget in dollar", key="tenant_budget")
                move_in_date = st.text_input("Move-in Date", key="tenant_move_in_date")
                if st.button("Submit", key="tenant_submit"):
                    st.session_state['user_type'] = 'tenant'
                    user_info = {
                        "name": name,
                        "property_type": property_type,
                        "budget_in_dollar": budget,
                        "move_in_date": move_in_date
                    }
                    save_user_metadata("tenant", user_info)  # Save the user info
                    st.session_state.expander_visible = False  # Hide the expander
                    return {
                        "user_type": user_type,
                        "information": user_info
                    }

            elif user_type == "Landlord":
                name = st.text_input("Name", key="landlord_name")
                property_type = st.text_input("Property Type", key="landlord_property_type")
                availability = st.text_input("Availability", key="landlord_availability")
                rental_status = st.text_input("Rental Status", key="landlord_rental_status")
                furnishing_details = st.text_input("Furnishing Details", key="landlord_furnishing_details")
                property_specific = st.text_input("Property specifics (floor, sq.ft etc.)", key='landlord_property_specific')
                if st.button("Submit", key="landlord_submit"):
                    st.session_state['user_type'] = 'landlord_for_rent'
                    user_info = {
                        "name": name,
                        "property_type": property_type,
                        "availability": availability,
                        "rental_status": rental_status,
                        "furnishing_details": furnishing_details,
                        "property_specifics": property_specific
                    }
                    save_user_metadata("landlord_for_rent", user_info)  # Save the user info
                    st.session_state.expander_visible = False  # Hide the expander
                    return {
                        "user_type": user_type,
                        "information": user_info
                    }
    return None

def bottom_container():
    with bottom():
        # Create a container for user input and the toggle buttons
        col1, col2 = st.columns([4, 1])  # Adjust column widths as needed
        with col1:
            st.write("")
            st.write("")
            user_prompt = st.chat_input("Write a question")
        with col2:
            # Use an empty container to eliminate spacing before the selectbox
            with st.empty():
                chat_mode = st.selectbox("Mode:", ["Normal", "Chat with Documents", "Chat with Agent"], key="chat_mode")
        
        if user_prompt:
            return user_prompt, chat_mode  # Return user prompt and chat mode
        else:
            return "", "Normal"  # Return default values if no input

async def main():
    st.header("🏢 REAL ESTATE CHATBOT")

    # Check if user info is already present in session state
    if "user_info" not in st.session_state or st.session_state['user_info'] is None:
        # Show the input form in an expander
        user_info = input_user_information()

        # Store user info in session state once submitted
        if user_info is not None:  # Check if user information was submitted
            st.session_state.user_info = user_info
            st.session_state.expander_visible = False  # Hide the expander after submission
    else:
        user_info = st.session_state.user_info

    if user_info is not None:
        user_prompt, chat_mode = bottom_container()  # Get user input and chat mode
        if user_prompt is not None and user_prompt != '':
            with st.container(border=True, height=500):
                chat_history = await read_chat_history()  # Read chat history asynchronously
                format_history = await format_chat_history_llamaindex(chat_history)
                display_chat_history(chat_history)
                with st.chat_message("HUMAN", avatar='./assets/user.png'):
                    st.markdown(user_prompt)

                if chat_mode == "Chat with Documents":
                    answer = await llamaindex_chatbot(user_prompt, format_history)  # Pass the toggle state
                elif chat_mode == "Chat with Agent":
                    answer = await crewai_agent_chat(user_prompt)  # Chat with the agent
                else:  # Normal chat
                    answer = chat_with_llm(st.session_state.user_info, user_prompt)

                with st.chat_message("AI", avatar='./assets/meta.png'):
                    st.write(answer)

                save_to_json(user_prompt, answer)
# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
