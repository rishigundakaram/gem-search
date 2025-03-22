import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from "react-router-dom";
import SearchContainer from "./containers/SearchContainer";
import About from "./pages/About";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";

const NavigationButton: React.FC = () => {
  const location = useLocation();
  // Determine the opposite page based on current location
  const isAboutPage = location.pathname === "/about";
  const targetPath = isAboutPage ? "/" : "/about";
  const buttonLabel = isAboutPage ? "gem-search" : "about";

  return (
    <Box sx={{ position: "fixed", top: 16, right: 16, zIndex: 1000 }}>
      <Button
        variant="contained"
        size="small"
        component={Link}
        to={targetPath}
        sx={{ textTransform: "none" }}
      >
        {buttonLabel}
      </Button>
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <NavigationButton />
      <Box sx={{ pt: 4 }}>
        <Routes>
          <Route path="/" element={<SearchContainer />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </Box>
    </Router>
  );
};

export default App;
