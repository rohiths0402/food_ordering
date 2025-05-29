import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Helmet from "../component/Helmet.jsx";
import { Container, Row, Col, ListGroup, ListGroupItem } from "reactstrap";
import "../styles/hero-selection.css";
import Category from "../component/UI/category/category.jsx";
import "../styles/home.css";
import featureImg01 from "../assets/service-01.png";
import featureImg02 from "../assets/service-02.png";
import featureImg03 from "../assets/service-03.png";

import foodCategoryImg01 from "../assets/hamburger.png";
import foodCategoryImg02 from "../assets/pizza.png";
import foodCategoryImg03 from "../assets/bread.png";

import ProductCard from "../component/UI/productCard/productCard.jsx";

import whyImg from "../assets/location.png";
import networkImg from "../assets/network (1).png";

import TestimonialSlider from "../component/UI/slider.jsx";

const featureData = [
  {
    title: "Quick Delivery",
    imgUrl: featureImg01,
    desc: "Lorem ipsum dolor, sit amet consectetur adipisicing elit. Minus, doloremque.",
  },
  {
    title: "Super Dine In",
    imgUrl: featureImg02,
    desc: "Lorem ipsum dolor, sit amet consectetur adipisicing elit. Minus, doloremque.",
  },
  {
    title: "Easy Pick Up",
    imgUrl: featureImg03,
    desc: "Lorem ipsum dolor, sit amet consectetur adipisicing elit. Minus, doloremque.",
  },
];

const Home = () => {
  const [category, setCategory] = useState("ALL");
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [hotPizza, setHotPizza] = useState([]);

  // Fetch products from backend with role & country headers
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const role = localStorage.getItem("role") || "guest";
        const country = localStorage.getItem("country") || "India";

        const response = await fetch("http://localhost:5000/food", {
          headers: {
            Role: role,
            Country: country,
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setProducts(data);
        setAllProducts(data);

        // Get top 4 pizzas
        const pizzaItems = data
          .filter((item) => item.category === "Pizza")
          .slice(0, 4);
        setHotPizza(pizzaItems);
      } catch (error) {
        console.error("Error fetching products:", error);
      }
    };

    fetchProducts();
  }, []);

  // Filter products by category
  useEffect(() => {
    if (category === "ALL") {
      setAllProducts(products);
    } else {
      const filtered = products.filter((item) => item.category === category);
      setAllProducts(filtered);
    }
  }, [category, products]);

  return (
    <Helmet title="Home">
      {/* Hero Section */}
      <section>
        <Container>
          <Row>
            <Col lg="6" md="6">
              <div className="hero__content">
                <h5 className="mb-3">Easy way to make an order</h5>
                <h1 className="mb-4 hero__title">
                  <span>HUNGRY?</span> Just wait <br /> food at
                  <span> your door</span>
                </h1>
                <p>
                  Lorem ipsum dolor sit amet, consectetur adipisicing elit. Qui
                  magni delectus tenetur autem, sint veritatis!
                </p>
                <div className="hero__btns d-flex align-items-center gap-5 mt-4">
                  <button className="order__btn d-flex align-items-center justify-content-between">
                    Order now <i className="ri-arrow-right-s-line"></i>
                  </button>
                  <button className="all__foods-btn">
                    <Link to="/foods">See all foods</Link>
                  </button>
                </div>
                <div className="hero__service d-flex align-items-center gap-5 mt-5">
                  <p className="d-flex align-items-center gap-2">
                    <span className="shipping__icon">
                      <i className="ri-car-line"></i>
                    </span>
                    No shipping charge
                  </p>
                  <p className="d-flex align-items-center gap-2">
                    <span className="shipping__icon">
                      <i className="ri-shield-check-line"></i>
                    </span>
                    100% secure checkout
                  </p>
                </div>
              </div>
            </Col>
            <Col lg="6" md="6">
              <div className="hero__img">
                <img src="/images/hero.png" alt="hero-img" className="w-100" />
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Category */}
      <section className="pt-0">
        <Category />
      </section>

      {/* Features */}
      <section>
        <Container>
          <Row>
            <Col lg="12" className="text-center">
              <h5 className="feature__subtitle mb-4">What we serve</h5>
              <h2 className="feature__title">Just sit back at home</h2>
              <h2 className="feature__title">
                we will <span>take care</span>
              </h2>
              <p className="mb-1 mt-4 feature__text">
                Lorem, ipsum dolor sit amet consectetur adipisicing elit. Dolor,
                officiis?
              </p>
              <p className="feature__text">
                Lorem ipsum dolor sit amet consectetur adipisicing elit.
                Aperiam, eius.
              </p>
            </Col>
            {featureData.map((item, index) => (
              <Col lg="4" md="6" sm="6" key={index} className="mt-5">
                <div className="feature__item text-center px-5 py-3">
                  <img
                    src={item.imgUrl}
                    alt="feature-img"
                    className="w-25 mb-3"
                  />
                  <h5 className="fw-bold mb-3">{item.title}</h5>
                  <p>{item.desc}</p>
                </div>
              </Col>
            ))}
          </Row>
        </Container>
      </section>

      {/* Popular Foods */}
      <section>
        <Container>
          <Row>
            <Col lg="12" className="text-center">
              <h2>Popular Foods</h2>
            </Col>
            <Col lg="12">
              <div className="food__category d-flex align-items-center justify-content-center gap-4">
                {["ALL", "BURGER", "PIZZA", "BREAD"].map((cat, idx) => (
                  <button
                    key={idx}
                    className={`d-flex align-items-center gap-2 ${category === cat ? "foodBtnActive" : ""}`}
                    onClick={() => setCategory(cat)}
                  >
                    {cat !== "ALL" && (
                      <img
                        src={
                          cat === "BURGER"
                            ? foodCategoryImg01
                            : cat === "PIZZA"
                              ? foodCategoryImg02
                              : foodCategoryImg03
                        }
                        alt={cat}
                      />
                    )}
                    {cat}
                  </button>
                ))}
              </div>
            </Col>

            {allProducts.map((item) => (
              <Col lg="3" md="4" sm="6" xs="6" key={item.id} className="mt-5">
                <ProductCard item={item} />
              </Col>
            ))}
          </Row>
        </Container>
      </section>

      {/* Why Us */}
      <section className="why__choose-us">
        <Container>
          <Row>
            <Col lg="6" md="6">
              <img src={whyImg} alt="why-tasty-treat" className="w-100" />
            </Col>
            <Col lg="6" md="6">
              <div className="why__tasty-treat">
                <h2 className="tasty__treat-title mb-4">
                  Why <span>Tasty Treat?</span>
                </h2>
                <p className="tasty__treat-desc">
                  Lorem ipsum dolor sit amet consectetur adipisicing elit.
                  Dolorum, minus...
                </p>
                <ListGroup className="mt-4">
                  {[
                    "Fresh and tasty foods",
                    "Quality support",
                    "Order from any location",
                  ].map((text, idx) => (
                    <ListGroupItem className="border-0 ps-0" key={idx}>
                      <p className="choose__us-title d-flex align-items-center gap-2">
                        <i className="ri-checkbox-circle-line"></i> {text}
                      </p>
                      <p className="choose__us-desc">
                        Lorem ipsum dolor sit amet consectetur adipisicing elit.
                      </p>
                    </ListGroupItem>
                  ))}
                </ListGroup>
              </div>
            </Col>
          </Row>
        </Container>
      </section>

      {/* Hot Pizza */}
      <section className="pt-0">
        <Container>
          <Row>
            <Col lg="12" className="text-center mb-5">
              <h2>Hot Pizza</h2>
            </Col>
            {hotPizza.map((item) => (
              <Col lg="3" md="4" sm="6" xs="6" key={item.id}>
                <ProductCard item={item} />
              </Col>
            ))}
          </Row>
        </Container>
      </section>

      {/* Testimonials */}
      <section>
        <Container>
          <Row>
            <Col lg="6" md="6">
              <div className="testimonial">
                <h5 className="testimonial__subtitle mb-4">Testimonial</h5>
                <h2 className="testimonial__title mb-4">
                  What our <span>customers</span> are saying
                </h2>
                <p className="testimonial__desc">
                  Lorem ipsum dolor sit amet consectetur, adipisicing elit.
                </p>
                <TestimonialSlider />
              </div>
            </Col>
            <Col lg="6" md="6">
              <img src={networkImg} alt="testimonial-img" className="w-100" />
            </Col>
          </Row>
        </Container>
      </section>
    </Helmet>
  );
};

export default Home;
