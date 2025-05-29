import React, { useState, useEffect } from "react";
import Helmet from "../component/Helmet";
import CommonSection from "../component/UI/commonSelection/commonSelection";
import { Container, Row, Col } from "reactstrap";
import ProductCard from "../component/UI/productCard/productCard";
import ReactPaginate from "react-paginate";
import "../styles/allfood.css";
import "../styles/pagination.css";

const AllFoods = () => {
  const [products, setProducts] = useState([]);
  const [allProducts, setAllProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [category, setCategory] = useState("ALL");
  const [pageNumber, setPageNumber] = useState(0);

  const token = localStorage.getItem("token"); // Make sure token is saved on login

  // Fetch food items from backend
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch("http://localhost:5000/food", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch food items");
        }

        const data = await response.json();
        setProducts(data);
        setAllProducts(data);
      } catch (error) {
        console.error("Error fetching food items:", error);
      }
    };

    fetchProducts();
  }, [token]);

  // Filter by category
  useEffect(() => {
    if (category === "ALL") {
      setAllProducts(products);
    } else {
      const filtered = products.filter((item) => item.category === category);
      setAllProducts(filtered);
    }
  }, [category, products]);

  // Search filter
  const searchedProduct = allProducts.filter((item) =>
    item.title.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  // Pagination
  const productPerPage = 12;
  const visitedPage = pageNumber * productPerPage;
  const displayPage = searchedProduct.slice(
    visitedPage,
    visitedPage + productPerPage,
  );
  const pageCount = Math.ceil(searchedProduct.length / productPerPage);
  const changePage = ({ selected }) => setPageNumber(selected);

  return (
    <Helmet title="All Foods">
      <CommonSection title="All Foods" />

      <section>
        <Container>
          <Row>
            <Col lg="6" md="6" sm="6" xs="12">
              <div className="search__widget d-flex align-items-center justify-content-between">
                <input
                  type="text"
                  placeholder="I'm looking for..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <span>
                  <i className="ri-search-line"></i>
                </span>
              </div>
            </Col>

            <Col lg="6" md="6" sm="6" xs="12" className="mb-5">
              <div className="sorting__widget text-end">
                <select
                  className="w-50"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="ALL">All</option>
                  <option value="Pizza">Pizza</option>
                  <option value="Burger">Burger</option>
                  <option value="Sushi">Sushi</option>
                  {/* Add more if needed */}
                </select>
              </div>
            </Col>

            {displayPage.map((item, index) => (
              <Col lg="3" md="4" sm="6" xs="6" key={index} className="mb-4">
                <ProductCard item={item} />
              </Col>
            ))}

            <div>
              <ReactPaginate
                pageCount={pageCount}
                onPageChange={changePage}
                previousLabel={"Prev"}
                nextLabel={"Next"}
                containerClassName="paginationBttns"
              />
            </div>
          </Row>
        </Container>
      </section>
    </Helmet>
  );
};

export default AllFoods;
