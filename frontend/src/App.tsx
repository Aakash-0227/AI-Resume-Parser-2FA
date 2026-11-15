
import { useState, type ChangeEvent, type FormEvent } from "react";
import "./App.css";

const API_URL = "http://localhost:8000";

interface ResumeResult {
  message: string;
  filename: string;
  extracted_data: {
    name: string | null;
    email: string | null;
    phone: string | null;
    qualification: string | null;
    skills: string[];
    experience: string | null;
  };
}

type Stage =
  | "resume"
  | "register"
  | "verify"
  | "complete"
  | "dashboard";

type Profile = Record<string, unknown>;

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ResumeResult | null>(null);

  const [stage, setStage] = useState<Stage>("resume");
  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");
  const [registerMessage, setRegisterMessage] = useState("");
  const [verifyMessage, setVerifyMessage] = useState("");
  const [loginMessage, setLoginMessage] = useState("");

  const [showLogin, setShowLogin] = useState(false);

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [otp, setOtp] = useState("");
  const [authToken, setAuthToken] = useState("");

  // Student profile states
  const [profileData, setProfileData] = useState<Profile | null>(null);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [profileMessage, setProfileMessage] = useState("");

  const [editFullName, setEditFullName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editQualification, setEditQualification] = useState("");
  const [editSkills, setEditSkills] = useState("");
  const [editExperience, setEditExperience] = useState("");

  // Extract JWT from API response.
  const extractToken = (data: unknown): string => {
    if (typeof data === "string") {
      return data.trim().replace(/^"|"$/g, "");
    }

    if (data && typeof data === "object") {
      const response = data as Record<string, unknown>;
      const token = response.access_token || response.token;

      return typeof token === "string" ? token : "";
    }

    return "";
  };

  // Parse API response safely.
  const parseResponse = async (response: Response): Promise<unknown> => {
    const responseText = await response.text();

    try {
      return JSON.parse(responseText);
    } catch {
      return responseText;
    }
  };

  // Get a readable error from an API response.
  const getErrorMessage = (data: unknown, fallback: string): string => {
    if (data && typeof data === "object") {
      const errorData = data as Record<string, unknown>;
      if (errorData.detail) return String(errorData.detail);
      if (errorData.message) return String(errorData.message);
    }

    if (typeof data === "string" && data.trim()) {
      return data;
    }

    return fallback;
  };

  // Convert profile values to editable strings.
  const profileValue = (profile: Profile, key: string): string => {
    const value = profile[key];
    if (value === null || value === undefined) return "";
    if (Array.isArray(value)) return value.join(", ");
    return String(value);
  };

  // Populate edit fields from the retrieved profile.
  const populateEditFields = (profile: Profile) => {
    setEditFullName(
      profileValue(profile, "full_name") ||
      profileValue(profile, "name")
    );

    setEditPhone(profileValue(profile, "phone"));
    setEditQualification(profileValue(profile, "qualification"));
    setEditSkills(profileValue(profile, "skills"));
    setEditExperience(profileValue(profile, "experience"));
  };

  // Select resume.
  const handleFileChange = (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) return;

    const extension = selectedFile.name
      .substring(selectedFile.name.lastIndexOf("."))
      .toLowerCase();

    if (![".pdf", ".docx"].includes(extension)) {
      setMessage("Please select a PDF or DOCX file.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setMessage("");
  };

  // Upload and parse resume.
  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select your resume first.");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/api/v1/resume/parse`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Resume parsing failed.")
        );
      }

      if (!data || typeof data !== "object") {
        throw new Error("Invalid response from resume parser.");
      }

      const resumeData = data as ResumeResult;

      setResult(resumeData);
      setFullName(resumeData.extracted_data.name || "");
      setPhone(resumeData.extracted_data.phone || "");

      setStage("register");
      setMessage("Resume parsed successfully!");

      setTimeout(() => {
        document.getElementById("onboarding")?.scrollIntoView({
          behavior: "smooth",
        });
      }, 150);
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Unable to parse resume."
      );
    } finally {
      setLoading(false);
    }
  };

  // Register a new user.
  const handleRegister = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setRegisterMessage("");

    if (password.length < 8) {
      setRegisterMessage(
        "Password must contain at least 8 characters."
      );
      return;
    }

    if (password !== confirmPassword) {
      setRegisterMessage("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/auth/register`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            full_name: fullName,
            email: email.trim().toLowerCase(),
            phone,
            password,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Registration failed.")
        );
      }

      setRegisterMessage(
        typeof data === "string"
          ? data
          : "Registration successful. Check your email for the OTP."
      );

      setPassword("");
      setConfirmPassword("");
      setOtp("");

      setStage("verify");

      setTimeout(() => {
        document.getElementById("onboarding")?.scrollIntoView({
          behavior: "smooth",
        });
      }, 150);
    } catch (error) {
      setRegisterMessage(
        error instanceof Error
          ? error.message
          : "Registration failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Verify email OTP.
  const handleVerify = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setVerifyMessage("");

    if (!/^\d{6}$/.test(otp)) {
      setVerifyMessage("Please enter a valid 6-digit OTP.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/auth/verify-2fa`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            channel: "email",
            otp,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "OTP verification failed.")
        );
      }

      const token = extractToken(data);

      if (token.split(".").length === 3) {
        setAuthToken(token);
      }

      setVerifyMessage("Email verified successfully!");
      setStage("complete");
    } catch (error) {
      setVerifyMessage(
        error instanceof Error
          ? error.message
          : "OTP verification failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Login existing user.
  const handleLogin = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setLoginMessage("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/v1/auth/login`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: loginEmail.trim().toLowerCase(),
            password: loginPassword,
          }),
        }
      );

      const data = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, "Login failed.")
        );
      }

      const token = extractToken(data);

      if (token.split(".").length !== 3) {
        throw new Error(
          "Login response did not contain a valid JWT token."
        );
      }

      setAuthToken(token);
      setLoginPassword("");
      setLoginMessage("Login successful!");

      setStage("complete");
      setShowLogin(false);

      setTimeout(() => {
        document.getElementById("onboarding")?.scrollIntoView({
          behavior: "smooth",
        });
      }, 150);
    } catch (error) {
      setLoginMessage(
        error instanceof Error
          ? error.message
          : "Login failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Access protected dashboard and retrieve profile.
  const handleDashboard = async () => {
    if (!authToken) {
      setVerifyMessage(
        "Please log in to obtain a dashboard access token."
      );
      return;
    }

    setLoading(true);
    setVerifyMessage("");
    setProfileMessage("");

    try {
      const dashboardResponse = await fetch(
        `${API_URL}/api/v1/dashboard/redirect`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const dashboardData = await parseResponse(dashboardResponse);

      if (!dashboardResponse.ok) {
        throw new Error(
          getErrorMessage(
            dashboardData,
            "Unable to access dashboard."
          )
        );
      }

      const profileResponse = await fetch(
        `${API_URL}/api/v1/profile`,
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
        }
      );

      const profile = await parseResponse(profileResponse);

      if (!profileResponse.ok) {
        throw new Error(
          getErrorMessage(profile, "Unable to load student profile.")
        );
      }

      if (
        !profile ||
        typeof profile !== "object" ||
        Array.isArray(profile)
      ) {
        throw new Error(
          "The profile API did not return a valid profile object."
        );
      }

      const receivedProfile = profile as Profile;

      setProfileData(receivedProfile);
      populateEditFields(receivedProfile);
      setIsEditingProfile(false);
      setStage("dashboard");

      setTimeout(() => {
        document.getElementById("student-dashboard")?.scrollIntoView({
          behavior: "smooth",
        });
      }, 100);
    } catch (error) {
      setVerifyMessage(
        error instanceof Error
          ? error.message
          : "Dashboard request failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Open profile editor.
  const handleEditProfile = () => {
    if (profileData) {
      populateEditFields(profileData);
    }

    setProfileMessage("");
    setIsEditingProfile(true);
  };

  // Save edited student profile using PATCH API.
  const handleSaveProfile = async (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    setProfileMessage("");

    if (!authToken) {
      setProfileMessage("Authentication token is missing. Please log in again.");
      return;
    }

    const skillsArray = editSkills
      .split(",")
      .map((skill) => skill.trim())
      .filter((skill) => skill.length > 0);

    setLoading(true);

    try {
      const updatedProfile = {
        full_name: editFullName.trim(),
        phone: editPhone.trim(),
        qualification: editQualification.trim(),
        skills: skillsArray,
        experience: editExperience.trim(),
      };

      const response = await fetch(
        `${API_URL}/api/v1/profile`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify(updatedProfile),
        }
      );

      const responseData = await parseResponse(response);

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            responseData,
            "Unable to update student profile."
          )
        );
      }

      // Use the returned profile when the API provides one.
      // Otherwise, update the displayed data from the submitted values.
      let updatedData: Profile = {
        ...(profileData || {}),
        ...updatedProfile,
      };

      if (
        responseData &&
        typeof responseData === "object" &&
        !Array.isArray(responseData)
      ) {
        updatedData = {
          ...updatedData,
          ...(responseData as Profile),
        };
      }

      setProfileData(updatedData);
      populateEditFields(updatedData);
      setIsEditingProfile(false);
      setProfileMessage("Profile updated successfully!");

    } catch (error) {
      setProfileMessage(
        error instanceof Error
          ? error.message
          : "Profile update failed."
      );
    } finally {
      setLoading(false);
    }
  };

  // Cancel profile editing.
  const handleCancelEdit = () => {
    if (profileData) {
      populateEditFields(profileData);
    }

    setIsEditingProfile(false);
    setProfileMessage("");
  };

  // Return to account access.
  const handleBackToAccount = () => {
    setStage("complete");
    setVerifyMessage("");
    setIsEditingProfile(false);

    setTimeout(() => {
      document.getElementById("onboarding")?.scrollIntoView({
        behavior: "smooth",
      });
    }, 100);
  };

  return (
    <div className="app">

      {/* Navigation */}
      <header className="navbar">
        <div className="brand">
          <div className="brand-icon">R</div>
          <span>
            Resume<span className="brand-highlight">AI</span>
          </span>
        </div>

        <nav>
          <a href="#home">Home</a>
          <a href="#upload">Resume Parser</a>
          <a href="#about">About</a>
        </nav>

        <button
          className="login-button"
          onClick={() =>
            document.getElementById("onboarding")?.scrollIntoView({
              behavior: "smooth",
            })
          }
        >
          Get Started
        </button>
      </header>

      <main id="home">

        {/* Hero */}
        <section className="hero">
          <div className="hero-content">
            <div className="tag">
              AI-POWERED ONBOARDING PLATFORM
            </div>

            <h1>
              Turn Your Resume Into
              <span> Opportunity.</span>
            </h1>

            <p>
              Upload your resume and let AI extract your
              professional information to simplify your
              registration and onboarding process.
            </p>

            <a href="#upload" className="primary-button">
              Parse Your Resume <span>→</span>
            </a>

            <div className="hero-features">
              <span>✓ PDF & DOCX Support</span>
              <span>✓ AI Information Extraction</span>
              <span>✓ Secure Onboarding</span>
            </div>
          </div>

          <div className="hero-visual">
            <div className="document-card">
              <div className="document-top">
                <div className="document-icon">📄</div>

                <div>
                  <strong>Resume Analysis</strong>
                  <small>AI document processing</small>
                </div>

                <span className="status">Ready</span>
              </div>

              <div className="document-line long"></div>
              <div className="document-line medium"></div>

              <div className="analysis-item">
                <span className="analysis-icon">👤</span>

                <div>
                  <strong>Personal Details</strong>
                  <small>Name, Email, Phone</small>
                </div>

                <span className="check">✓</span>
              </div>

              <div className="analysis-item">
                <span className="analysis-icon">💼</span>

                <div>
                  <strong>Professional Skills</strong>
                  <small>Skills and Experience</small>
                </div>

                <span className="check">✓</span>
              </div>

              <div className="analysis-item">
                <span className="analysis-icon">🎓</span>

                <div>
                  <strong>Qualification</strong>
                  <small>Education details</small>
                </div>

                <span className="check">✓</span>
              </div>

              <div className="ai-label">✦ Powered by AI</div>
            </div>
          </div>
        </section>

        {/* Resume Upload */}
        <section className="upload-section" id="upload">
          <div className="section-heading">
            <span className="tag">STEP 1</span>
            <h2>Upload Your Resume</h2>
            <p>Let our AI extract your details automatically.</p>
          </div>

          <div className="upload-card">
            <div className="upload-icon">↑</div>

            <h3>Select your resume</h3>
            <p>Choose a PDF or DOCX file from your computer.</p>

            <label className="file-button">
              Browse Files

              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
              />
            </label>

            {file && (
              <div className="selected-file">
                <span>📄</span>
                <span>{file.name}</span>
                <span>✓</span>
              </div>
            )}

            <button
              className="upload-button"
              onClick={handleUpload}
              disabled={loading}
            >
              {loading ? "Processing..." : "Upload & Parse Resume →"}
            </button>

            {message && <p className="message">{message}</p>}

            {result && (
              <div className="result-card">
                <h3>Extracted Resume Information</h3>

                <p>
                  <strong>Name:</strong>{" "}
                  {result.extracted_data.name || "Not found"}
                </p>

                <p>
                  <strong>Email:</strong>{" "}
                  {result.extracted_data.email || "Not found"}
                </p>

                <p>
                  <strong>Phone:</strong>{" "}
                  {result.extracted_data.phone || "Not found"}
                </p>

                <p>
                  <strong>Qualification:</strong>{" "}
                  {result.extracted_data.qualification || "Not found"}
                </p>

                <p>
                  <strong>Experience:</strong>{" "}
                  {result.extracted_data.experience || "Not found"}
                </p>

                <p><strong>Skills:</strong></p>

                <div className="skills-list">
                  {result.extracted_data.skills.length > 0
                    ? result.extracted_data.skills.map(
                        (skill, index) => (
                          <span key={index}>{skill}</span>
                        )
                      )
                    : "No skills found"}
                </div>

                <button
                  className="upload-button"
                  onClick={() => {
                    setStage("register");
                    setShowLogin(false);

                    document.getElementById("onboarding")?.scrollIntoView({
                      behavior: "smooth",
                    });
                  }}
                >
                  Continue to Registration →
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Account Onboarding */}
        <section className="upload-section" id="onboarding">
          <div className="section-heading">
            <span className="tag">STEP 2</span>
            <h2>Account Access</h2>
            <p>
              Register a new account or log in to an existing account.
            </p>
          </div>

          {/* Login Form */}
          {showLogin ? (
            <form
              className="upload-card registration-form"
              onSubmit={handleLogin}
            >
              <div className="upload-icon">🔐</div>

              <h3>Welcome Back</h3>
              <p>
                Login using your registered email and password.
              </p>

              <label>Email Address</label>

              <input
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                placeholder="Enter registered email"
                required
              />

              <label>Password</label>

              <input
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />

              <button
                className="upload-button"
                type="submit"
                disabled={loading}
              >
                {loading ? "Logging in..." : "Login →"}
              </button>

              {loginMessage && (
                <p className="message">{loginMessage}</p>
              )}

              <p>
                New user?{" "}

                <button
                  type="button"
                  className="text-button"
                  onClick={() => {
                    setShowLogin(false);
                    setLoginMessage("");
                  }}
                >
                  Back to registration
                </button>
              </p>
            </form>

          ) : stage === "resume" ? (
            <div className="upload-card">
              <h3>Already have an account?</h3>

              <p>
                You can log in directly without uploading your resume again.
              </p>

              <button
                className="upload-button"
                onClick={() => {
                  setLoginEmail(email);
                  setShowLogin(true);
                  setLoginMessage("");
                }}
              >
                Login with Email & Password →
              </button>

              <p className="message">
                New users can upload a resume above to continue registration.
              </p>
            </div>

          ) : stage === "register" ? (
            <form
              className="upload-card registration-form"
              onSubmit={handleRegister}
            >
              <h3>Create Your Account</h3>

              <label>Full Name</label>

              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                required
              />

              <label>Email Address</label>

              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email address"
                required
              />

              <label>Phone Number</label>

              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="Enter your phone number"
                required
              />

              <label>Password</label>

              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Create a password (minimum 8 characters)"
                minLength={8}
                required
              />

              <label>Confirm Password</label>

              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your password"
                minLength={8}
                required
              />

              <button
                className="upload-button"
                type="submit"
                disabled={loading}
              >
                {loading ? "Creating Account..." : "Create Account →"}
              </button>

              {registerMessage && (
                <p className="message">{registerMessage}</p>
              )}

              <p>
                Already have an account?{" "}

                <button
                  type="button"
                  className="text-button"
                  onClick={() => {
                    setLoginEmail(email);
                    setShowLogin(true);
                    setLoginMessage("");
                  }}
                >
                  Login here
                </button>
              </p>
            </form>

          ) : stage === "verify" ? (
            <form
              className="upload-card registration-form"
              onSubmit={handleVerify}
            >
              <div className="upload-icon">🔐</div>

              <h3>Verify Your Email</h3>

              <p>Enter the six-digit OTP sent to:</p>
              <p><strong>{email}</strong></p>

              <label>Email OTP</label>

              <input
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={otp}
                onChange={(e) =>
                  setOtp(
                    e.target.value.replace(/\D/g, "").slice(0, 6)
                  )
                }
                placeholder="Enter 6-digit OTP"
                required
              />

              <button
                className="upload-button"
                type="submit"
                disabled={loading}
              >
                {loading ? "Verifying..." : "Verify OTP →"}
              </button>

              {verifyMessage && (
                <p className="message">{verifyMessage}</p>
              )}
            </form>

          ) : stage === "complete" ? (
            <div className="upload-card">
              <div className="upload-icon">✓</div>

              <h3>Account Access Successful</h3>

              <p>Your account has been authenticated.</p>

              <button
                className="upload-button"
                onClick={handleDashboard}
                disabled={loading}
              >
                {loading ? "Loading Dashboard..." : "Continue to Dashboard →"}
              </button>

              {verifyMessage && (
                <p className="message">{verifyMessage}</p>
              )}
            </div>
          ) : null}
        </section>

        {/* Student Dashboard */}
        {stage === "dashboard" && (
          <section
            className="upload-section"
            id="student-dashboard"
          >
            <div className="section-heading">
              <span className="tag">STUDENT PORTAL</span>

              <h2>Welcome to Your Dashboard</h2>

              <p>
                Your account is authenticated. Manage your student profile below.
              </p>
            </div>

            <div className="upload-card dashboard-card">
              <div className="upload-icon">👤</div>

              <h3>Student Profile</h3>

              {profileData && (
                <>
                  {!isEditingProfile ? (
                    <>
                      <div
                        className="profile-data"
                        style={{
                          textAlign: "left",
                          width: "100%",
                          overflowX: "auto",
                          marginTop: "20px",
                        }}
                      >
                        {Object.entries(profileData).map(
                          ([key, value]) => (
                            <div
                              key={key}
                              style={{
                                padding: "12px",
                                borderBottom: "1px solid #eeeeee",
                              }}
                            >
                              <strong
                                style={{
                                  display: "block",
                                  marginBottom: "6px",
                                  textTransform: "capitalize",
                                }}
                              >
                                {key.replace(/_/g, " ")}
                              </strong>

                              <span>
                                {Array.isArray(value)
                                  ? value.join(", ")
                                  : value !== null &&
                                      typeof value === "object"
                                    ? JSON.stringify(value)
                                    : String(value ?? "Not available")}
                              </span>
                            </div>
                          )
                        )}
                      </div>

                      <button
                        className="upload-button"
                        onClick={handleEditProfile}
                        style={{ marginTop: "24px" }}
                      >
                        ✏️ Edit Student Profile
                      </button>
                    </>
                  ) : (
                    <form
                      className="registration-form"
                      onSubmit={handleSaveProfile}
                      style={{
                        width: "100%",
                        marginTop: "20px",
                        textAlign: "left",
                      }}
                    >
                      <h3>Edit Your Information</h3>

                      <label>Full Name</label>

                      <input
                        type="text"
                        value={editFullName}
                        onChange={(e) =>
                          setEditFullName(e.target.value)
                        }
                        placeholder="Enter your full name"
                        required
                      />

                      <label>Phone Number</label>

                      <input
                        type="tel"
                        value={editPhone}
                        onChange={(e) =>
                          setEditPhone(e.target.value)
                        }
                        placeholder="Enter phone number"
                        required
                      />

                      <label>Qualification</label>

                      <input
                        type="text"
                        value={editQualification}
                        onChange={(e) =>
                          setEditQualification(e.target.value)
                        }
                        placeholder="Enter qualification"
                      />

                      <label>Skills</label>

                      <textarea
                        value={editSkills}
                        onChange={(e) =>
                          setEditSkills(e.target.value)
                        }
                        placeholder="Enter skills separated by commas"
                        rows={4}
                        style={{
                          width: "100%",
                          padding: "14px",
                          border: "1px solid #dddddd",
                          borderRadius: "8px",
                          fontSize: "14px",
                          marginBottom: "16px",
                          resize: "vertical",
                          fontFamily: "inherit",
                        }}
                      />

                      <p
                        style={{
                          fontSize: "12px",
                          color: "#777777",
                        }}
                      >
                        Example: Python, FastAPI, Machine Learning, SQL
                      </p>

                      <label>Experience</label>

                      <textarea
                        value={editExperience}
                        onChange={(e) =>
                          setEditExperience(e.target.value)
                        }
                        placeholder="Enter your experience"
                        rows={4}
                        style={{
                          width: "100%",
                          padding: "14px",
                          border: "1px solid #dddddd",
                          borderRadius: "8px",
                          fontSize: "14px",
                          marginBottom: "16px",
                          resize: "vertical",
                          fontFamily: "inherit",
                        }}
                      />

                      <div
                        style={{
                          display: "flex",
                          gap: "12px",
                          flexWrap: "wrap",
                        }}
                      >
                        <button
                          className="upload-button"
                          type="submit"
                          disabled={loading}
                          style={{ flex: 1 }}
                        >
                          {loading ? "Saving..." : "Save Profile Changes"}
                        </button>

                        <button
                          className="upload-button"
                          type="button"
                          onClick={handleCancelEdit}
                          disabled={loading}
                          style={{
                            flex: 1,
                            background: "#777777",
                          }}
                        >
                          Cancel
                        </button>
                      </div>
                    </form>
                  )}
                </>
              )}

              {profileMessage && (
                <p className="message">{profileMessage}</p>
              )}

              <button
                className="upload-button"
                onClick={handleBackToAccount}
                style={{ marginTop: "24px" }}
              >
                Back to Account Access
              </button>
            </div>
          </section>
        )}

        {/* Features */}
        <section className="features-section" id="about">
          <div className="section-heading">
            <span className="tag">OUR WORKFLOW</span>

            <h2>Simple. Smart. Secure.</h2>

            <p>
              A streamlined process from resume upload to onboarding.
            </p>
          </div>

          <div className="feature-grid">
            <div className="feature-card">
              <span>📄</span>

              <h3>Resume Parsing</h3>

              <p>
                Extract personal, educational and professional details.
              </p>
            </div>

            <div className="feature-card">
              <span>🔐</span>

              <h3>Two-Factor Authentication</h3>

              <p>
                Verify user identity through secure authentication.
              </p>
            </div>

            <div className="feature-card">
              <span>👤</span>

              <h3>Student Dashboard</h3>

              <p>
                Review and manage your extracted profile information.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer>
        <p>
          © 2026 ResumeAI | AI Resume Parser & Secure Onboarding
        </p>
      </footer>
    </div>
  );
}

export default App;
