import React, { useRef } from "react";
import { useNavigate } from "react-router-dom";
import Helmet from "../component/Helmet";
import CommonSection from "../component/UI/commonSelection/commonSelection";
import { Container, Row, Col } from "reactstrap";
import { Link } from "react-router-dom";

const Login = () => {
  const loginNameRef = useRef();
  const loginPasswordRef = useRef();
  const navigate = useNavigate();

  // Function to get country from user's geolocation
  const getCountryFromGeolocation = () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          try {
            // Use geocode.xyz to get country name from coordinates
            const res = await fetch(
              `https://geocode.xyz/${latitude},${longitude}?geoit=json`,
            );
            const data = await res.json();
            if (data && data.country) {
              resolve(data.country);
            } else {
              resolve(null);
            }
          } catch {
            resolve(null);
          }
        },
        () => {
          resolve(null); // Permission denied or error
        },
      );
    });
  };

  const submitHandler = async (e) => {
    e.preventDefault();
    const username = loginNameRef.current.value.trim();
    const password = loginPasswordRef.current.value.trim();

    if (!username || !password) {
      alert("Please enter username and password");
      return;
    }

    try {
      const response = await fetch("http://localhost:5000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        alert("Login failed: Invalid username or password");
        return;
      }

      const data = await response.json();
      const user = data.user;

      // Try to get geolocation country, fallback to server country
      let country = user.country;
      const geoCountry = await getCountryFromGeolocation();
      if (geoCountry) {
        country = geoCountry;
      }

      // Save info to localStorage
      localStorage.setItem("userId", user.id || "");
      localStorage.setItem("username", user.username || "");
      localStorage.setItem("role", user.role || "");
      localStorage.setItem("country", country || "");

      // Redirect to home page
      navigate("/home");
    } catch (error) {
      alert("An error occurred. Please try again.");
      console.error(error);
    }
  };

  return (
    <Helmet title="Login">
      <CommonSection title="Login" />
      <section>
        <Container>
          <Row>
            <Col lg="6" md="6" sm="12" className="m-auto text-center">
              <form className="form mb-5" onSubmit={submitHandler}>
                <div className="form__group">
                  <input
                    type="text"
                    placeholder="Username"
                    required
                    ref={loginNameRef}
                  />
                </div>
                <div className="form__group">
                  <input
                    type="password"
                    placeholder="Password"
                    required
                    ref={loginPasswordRef}
                  />
                </div>
                <button type="submit" className="addTOCart__btn">
                  Login
                </button>
              </form>
              <Link to="/register">
                Don't have an account? Create an account
              </Link>
            </Col>
          </Row>
        </Container>
      </section>
    </Helmet>
  );
};

export default Login;
