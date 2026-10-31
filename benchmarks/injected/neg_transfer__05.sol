pragma solidity 0.8.20;

contract Safe5979 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        supply += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        payable(msg.sender).transfer(amount);
        credit[msg.sender] -= amount;
        supply -= amount;
    }
}
