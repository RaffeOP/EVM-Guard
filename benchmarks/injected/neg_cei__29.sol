pragma solidity 0.8.20;

contract Pool5486 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        credit[msg.sender] -= amount;
        total -= amount;
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
    }

    function ownerOf_() public view returns (address) { return owner; }
}
