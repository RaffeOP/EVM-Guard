pragma solidity 0.8.20;

contract Fund5616 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }

    function ownerOf_() public view returns (address) { return owner; }
}
