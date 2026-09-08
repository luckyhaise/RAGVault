import  { useState } from "react";
import { requestCreateAccount, verifyAndCreateAccount } from "../api/auth";
import type { FormEvent, ChangeEvent } from "react";
import type { CreateAccount } from "../types/auth_types";

export default function CreateAccountForm() {
  const [formData, setFormData] = useState<CreateAccount>({
    user_name: "",
    email: "",
    phone:"",
    password: "",
    name: "",
    otp: "",
    otp_id: "",
  }); 
  const [otpStep, setOtpStep] = useState(false);
  function handleChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const { name, value } = event.target;

    setFormData((previous) => ({ ...previous, [name]: value, }));
  }

   async function handleCreateRequest(
      event: FormEvent<HTMLFormElement>
    ) {
      event.preventDefault();
      try {
        const result = await requestCreateAccount({
          user_name: formData.user_name,
          name: formData.name,
          email: formData.email,
          password: formData.password,
          phone: formData.phone
        
        });
        setFormData((previous) => ({...previous,otp_id:result.otp_id}))
        setOtpStep(true);
      }catch (error) {
        console.error(error)
      
      
}
}
  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    try {
      const result = await verifyAndCreateAccount(formData)

      console.log(result)
    } catch (error) {
      console.error(error)
      
    }
  }
  return (
    <form
         onSubmit={
           otpStep
             ? handleSubmit
             : handleCreateRequest
         }
       >
         {!otpStep && (
           <>
             <input
               name="name"
               placeholder="Name"
               value={formData.name}
               onChange={handleChange}
             />
   
             <input
               name="user_name"
               placeholder="Username"
               value={formData.user_name}
               onChange={handleChange}
             />
   
             <input
               name="email"
               type="email"
               placeholder="Email"
               value={formData.email}
               onChange={handleChange}
          />
          <input
                    name="phone"
                    type="tel"
                    placeholder="Phone Number"
                    value={formData.phone}
                    onChange={handleChange}
          />
          
   
             <input
               name="password"
               type="password"
               placeholder="Password"
               value={formData.password}
               onChange={handleChange}
             />
   
             <button type="submit">
               Create Account
             </button>
           </>
         )}
   
         {otpStep && (
           <>
             <input
               name="otp"
               placeholder="Enter OTP"
               value={formData.otp}
               onChange={handleChange}
             />
   
             <button type="submit">
               Verify Account
             </button>
           </>
         )}
       </form>
     );
}